from . import db, mysql
import MySQLdb

from .models import (
    Campaign, CampaignEventType, CampaignStatusEnum,
    Organisation, Tier, UserAccount,
)

# Statuses a fundraiser is allowed to switch between.
# pending / rejected / suspended belong to administrators.
FUNDRAISER_STATUSES = ('active', 'paused', 'closed')

# UML column
CAMPAIGN_COLUMNS = """
    c.id,
    c.orgId          AS org_id,
    c.title,
    c.goalAmount     AS goal_amount,
    c.amountRaised   AS amount_raised,
    c.status,
    c.location,
    c.eventDate      AS event_date,
    c.eventStartTime AS event_start_time,
    c.eventEndTime   AS event_end_time,
    c.overview,
    c.description,
    c.bannerImageUrl AS banner_image_url,
    c.isFeatured     AS is_featured,
    c.createdBy      AS created_by,
    c.createdDate    AS created_date,
    c.updatedDate    AS updated_date,
    c.publishDate    AS publish_date,
    c.eventType      AS event_type,
    o.name           AS organisation_name
"""



def query(sql, params=(), one=False):
    """Run a SELECT. Returns a list of dicts, or one dict/None when one=True."""
    cur = mysql.connection.cursor()
    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
        if one:
            return rows[0] if rows else None
        return rows
    finally:
        cur.close()


def execute(sql, params=()):
    """Run INSERT / UPDATE / DELETE. Returns (rows_matched, last_insert_id)."""
    cur = mysql.connection.cursor()
    try:
        cur.execute(sql, params)
        mysql.connection.commit()
        return cur.rowcount, cur.lastrowid
    except MySQLdb.Error:
        mysql.connection.rollback()
        raise
    finally:
        cur.close()


def _ensure_organisation(account_id):
    """
    Campaign.orgId is required. Use the account's organisation, or create one named
    after the account the first time that fundraiser creates a campaign.
    """
    account = query('SELECT username, orgId FROM accounts WHERE id = %s',
                    (account_id,), one=True)
    if account is None:
        return None
    if account['orgId']:
        return account['orgId']
    _, org_id = execute('INSERT INTO organisations (name) VALUES (%s)', (account['username'],))
    execute('UPDATE accounts SET orgId = %s WHERE id = %s', (org_id, account_id))
    return org_id



# Campaigns
def get_owned_campaigns(fundraiser_id):
    """All campaigns this fundraiser created, with the donation count."""
    return query(
        f"""
        SELECT {CAMPAIGN_COLUMNS}, COUNT(d.id) AS donor_count
        FROM campaigns c
        JOIN organisations o ON o.id = c.orgId
        LEFT JOIN donations d ON d.campaignId = c.id
        WHERE c.createdBy = %s
        GROUP BY c.id, o.name
        ORDER BY c.createdDate DESC, c.id DESC
        """,
        (fundraiser_id,),
    )


def get_campaign_for_owner(campaign_id, fundraiser_id):
    """One campaign, only if this fundraiser created it (else None)."""
    return query(
        f"""
        SELECT {CAMPAIGN_COLUMNS}, COUNT(d.id) AS donor_count
        FROM campaigns c
        JOIN organisations o ON o.id = c.orgId
        LEFT JOIN donations d ON d.campaignId = c.id
        WHERE c.id = %s AND c.createdBy = %s
        GROUP BY c.id, o.name
        """,
        (campaign_id, fundraiser_id),
        one=True,
    )


def add_campaign(fundraiser_id, title, overview, description, location, goal_amount,
                 event_date=None, event_start_time=None, event_end_time=None,
                 event_type=None, banner_image_url=None, tiers=None):
    """
    Create a campaign. It starts as 'pending' until an administrator approves it.
    tiers: optional list of {'name', 'amount', 'benefits'} saved with the campaign.
    """
    org_id = _ensure_organisation(fundraiser_id)
    if org_id is None:
        raise ValueError('Unknown account.')
    _, new_id = execute(
        """
        INSERT INTO campaigns
            (orgId, createdBy, title, goalAmount, status, location, eventDate,
             eventStartTime, eventEndTime, overview, description, bannerImageUrl,
             isFeatured, eventType)
        VALUES (%s, %s, %s, %s, 'pending', %s, %s, %s, %s, %s, %s, %s, 0, %s)
        """,
        (org_id, fundraiser_id, title, goal_amount, location, event_date,
         event_start_time, event_end_time, overview, description, banner_image_url,
         event_type),
    )
    if tiers:
        replace_tiers(new_id, fundraiser_id, tiers)
    return new_id


def update_campaign(campaign_id, fundraiser_id, title, overview, description,
                    location, goal_amount, event_date=None, event_start_time=None,
                    event_end_time=None, event_type=None, banner_image_url=None):
    """
    Edit campaign details. Returns True only if the fundraiser created the campaign.
    banner_image_url=None keeps the existing banner.
    """
    matched, _ = execute(
        """
        UPDATE campaigns
        SET title = %s, overview = %s, description = %s, location = %s,
            goalAmount = %s, eventDate = %s, eventStartTime = %s, eventEndTime = %s,
            eventType = %s, bannerImageUrl = COALESCE(%s, bannerImageUrl)
        WHERE id = %s AND createdBy = %s
        """,
        (title, overview, description, location, goal_amount, event_date,
         event_start_time, event_end_time, event_type, banner_image_url,
         campaign_id, fundraiser_id),
    )
    return matched == 1


def update_campaign_status(campaign_id, fundraiser_id, new_status):
    """
    Fundraiser status change. Only active / paused / closed are allowed, and only
    when the campaign is currently in one of those states, so a fundraiser can never
    override an administrator's pending, rejected or suspended decision.
    """
    if new_status not in FUNDRAISER_STATUSES:
        return False
    matched, _ = execute(
        """
        UPDATE campaigns
        SET status = %s
        WHERE id = %s AND createdBy = %s
          AND status IN ('active', 'paused', 'closed')
        """,
        (new_status, campaign_id, fundraiser_id),
    )
    return matched == 1


def delete_campaign(campaign_id, fundraiser_id):
    """
    Delete a campaign the fundraiser created. Campaigns that already received donations
    cannot be deleted (close them instead). Posts are removed by ON DELETE CASCADE.
    """
    deleted, _ = execute(
        """
        DELETE FROM campaigns
        WHERE id = %s AND createdBy = %s
          AND NOT EXISTS (SELECT 1 FROM donations d WHERE d.campaignId = campaigns.id)
        """,
        (campaign_id, fundraiser_id),
    )
    return deleted == 1


# Tiers (table: tiers; ownership checked through the parent campaign)

def get_tiers(campaign_id, fundraiser_id):
    """Tiers of a campaign this fundraiser created, cheapest first."""
    return query(
        """
        SELECT t.id, t.campaignId AS campaign_id, t.name, t.amount, t.benefits
        FROM tiers t
        JOIN campaigns c ON c.id = t.campaignId
        WHERE t.campaignId = %s AND c.createdBy = %s
        ORDER BY t.amount, t.id
        """,
        (campaign_id, fundraiser_id),
    )


def get_public_tiers(campaign_id):
    """Tiers of any campaign, for the supporter donation page (no ownership check)."""
    return query(
        """
        SELECT id, campaignId AS campaign_id, name, amount, benefits
        FROM tiers WHERE campaignId = %s ORDER BY amount, id
        """,
        (campaign_id,),
    )


def get_public_campaign(campaign_id=None):
    """Return an active campaign with its organisation, creator, and donor tiers."""
    campaign_filter = 'AND c.id = %s' if campaign_id is not None else ''
    params = (campaign_id,) if campaign_id is not None else ()
    
    row = query(
        f"""
        SELECT 
            c.id, c.title, c.goalAmount AS goal_amount,
            c.amountRaised AS amount_raised, c.status,
            c.location, c.eventDate AS event_date,
            c.eventStartTime AS event_start_time,
            c.eventEndTime AS event_end_time, c.overview,
            c.description, c.bannerImageUrl AS banner_image_url,
            c.isFeatured AS is_featured, c.createdDate AS created_date,
            c.updatedDate AS updated_date, c.publishDate AS publish_date,
            c.eventType AS event_type,

            supporter_count.supporter_count,

            o.id AS organisation_id,
            o.name AS organisation_name,
            o.description AS organisation_description,

            a.id AS creator_id,
            a.username AS creator_username,
            a.firstName AS creator_firstname,
            a.surName AS creator_surname,
            a.email AS creator_email,
            a.phone AS creator_phone,
            a.role AS creator_role,
            a.accountStatus AS creator_account_status,
            a.created_at AS creator_created_at,

            creator_org.id AS creator_org_id,
            creator_org.name AS creator_org_name,
            creator_org.description AS creator_org_description

        FROM campaigns c
        JOIN organisations o ON o.id = c.orgId
        JOIN accounts a ON a.id = c.createdBy
        LEFT JOIN organisations creator_org ON creator_org.id = a.orgId

        LEFT JOIN (
            SELECT campaignId, COUNT(*) AS supporter_count
            FROM donations
            GROUP BY campaignId
        ) supporter_count ON supporter_count.campaignId = c.id

        WHERE c.status = 'Active' {campaign_filter}
        ORDER BY c.isFeatured DESC, c.eventDate ASC, c.id DESC
        LIMIT 1;

        """,
        params,
        one=True,
    )
    if row is None:
        return None

    organisation = Organisation(
        id=row['organisation_id'],
        name=row['organisation_name'],
        description=row['organisation_description'] or '',
        logo_url='',
    )
    creator_info = db._user_info_from_row(row, 'creator')
    tiers = [
        Tier(
            id=tier['id'],
            name=tier['name'],
            amount=float(tier['amount']),
            benefits=tier['benefits'],
        )
        for tier in get_public_tiers(row['id'])
    ]
    return Campaign(
        _id=row['id'],
        _title=row['title'],
        _goal_amount=float(row['goal_amount']),
        _amount_raised=float(row['amount_raised']),
        _status=CampaignStatusEnum(row['status']),
        _location=row['location'],
        _event_date=row['event_date'],
        _event_start_time=row['event_start_time'],
        _event_end_time=row['event_end_time'],
        _overview=row['overview'],
        _description=row['description'],
        _banner_image_url=row['banner_image_url'] or '',
        _created_by=UserAccount(
            username=row['creator_username'],
            password='',
            info=creator_info,
        ),
        _organisation=organisation,
        _event_type=CampaignEventType(row['event_type']),
        _is_featured=bool(row['is_featured']),
        _tiers=tiers,
        _created_date=row['created_date'],
        _updated_date=row['updated_date'],
        _publish_date=row['publish_date'],
        supporter_count=row['supporter_count'],
    )


def replace_tiers(campaign_id, fundraiser_id, tiers):
    """
    Save the full list of tiers for a campaign in one transaction (old ones are
    replaced). Returns False, changing nothing, unless the fundraiser created it.
    tiers: list of {'name': str, 'amount': Decimal/number, 'benefits': str}
    """
    db = mysql.connection
    cur = db.cursor()
    try:
        cur.execute('SELECT 1 FROM campaigns WHERE id = %s AND createdBy = %s',
                    (campaign_id, fundraiser_id))
        if cur.fetchone() is None:
            return False
        cur.execute('DELETE FROM tiers WHERE campaignId = %s', (campaign_id,))
        if tiers:
            cur.executemany(
                'INSERT INTO tiers (campaignId, name, amount, benefits) VALUES (%s, %s, %s, %s)',
                [(campaign_id, t['name'], t['amount'], t['benefits']) for t in tiers],
            )
        db.commit()
        return True
    except MySQLdb.Error:
        db.rollback()
        raise
    finally:
        cur.close()



# Posts / updates (ownership checked through the parent campaign)

def get_posts(campaign_id, fundraiser_id):
    return query(
        """
        SELECT p.*
        FROM posts p
        JOIN campaigns c ON c.id = p.campaignId
        WHERE p.campaignId = %s AND c.createdBy = %s
        ORDER BY p.createdDate DESC
        """,
        (campaign_id, fundraiser_id),
    )


def add_post(campaign_id, fundraiser_id, title, message, image_path=''):
    """INSERT ... SELECT inserts nothing unless the campaign belongs to the fundraiser."""
    inserted, _ = execute(
        """
        INSERT INTO posts (campaignId, title, message, image_path)
        SELECT c.id, %s, %s, %s
        FROM campaigns c
        WHERE c.id = %s AND c.createdBy = %s
        """,
        (title, message, image_path, campaign_id, fundraiser_id),
    )
    return inserted == 1


def update_post(post_id, fundraiser_id, title, message):
    matched, _ = execute(
        """
        UPDATE posts p
        JOIN campaigns c ON c.id = p.campaignId
        SET p.title = %s, p.message = %s
        WHERE p.id = %s AND c.createdBy = %s
        """,
        (title, message, post_id, fundraiser_id),
    )
    return matched == 1


def delete_post(post_id, fundraiser_id):
    deleted, _ = execute(
        """
        DELETE p FROM posts p
        JOIN campaigns c ON c.id = p.campaignId
        WHERE p.id = %s AND c.createdBy = %s
        """,
        (post_id, fundraiser_id),
    )
    return deleted == 1



# Donations and statistics

def get_donations(campaign_id, fundraiser_id):
    """Donation history for a campaign this fundraiser created, newest first."""
    return query(
        """
        SELECT d.id, d.amount, d.createdDate AS created_at,
               d.notes AS message, d.isAnonymous AS is_anonymous,
               t.name AS tier_name,
               CASE WHEN d.isAnonymous = 1 THEN 'Anonymous Supporter'
                    ELSE CONCAT_WS(' ', a.firstName, a.surName) END AS donor_name
        FROM donations d
        JOIN campaigns c ON c.id = d.campaignId
        LEFT JOIN accounts a ON a.id = d.accountId
        LEFT JOIN tiers t ON t.id = d.tierId
        WHERE d.campaignId = %s AND c.createdBy = %s
        ORDER BY d.createdDate DESC, d.id DESC
        """,
        (campaign_id, fundraiser_id),
    )


def get_campaign_stats(campaign_id, fundraiser_id):
    """Dynamically generated statistics, calculated by the database."""
    row = query(
        """
        SELECT c.goalAmount                AS goal,
               COALESCE(SUM(d.amount), 0)  AS raised,
               COUNT(d.id)                 AS donor_count,
               COALESCE(AVG(d.amount), 0)  AS average,
               COALESCE(MAX(d.amount), 0)  AS largest,
               MAX(d.createdDate)           AS last_donation
        FROM campaigns c
        LEFT JOIN donations d ON d.campaignId = c.id
        WHERE c.id = %s AND c.createdBy = %s
        GROUP BY c.id
        """,
        (campaign_id, fundraiser_id),
        one=True,
    )
    if row is None:
        return None

    # MySQL returns DECIMAL values as Python Decimal; convert to float for easy maths
    goal = float(row['goal'] or 0)
    raised = float(row['raised'])
    return {
        'goal': goal,
        'raised': raised,
        'remaining': max(goal - raised, 0),
        'percent': min(round(raised / goal * 100, 1), 100) if goal else 0,
        'donor_count': row['donor_count'],
        'average': round(float(row['average']), 2),
        'largest': float(row['largest']),
        'last_donation': row['last_donation'],
    }


def get_donations_by_day(campaign_id, fundraiser_id):
    """Daily totals, handy for a chart of donations over time."""
    return query(
        """
        SELECT DATE(d.createdDate) AS day,
               SUM(d.amount)      AS total,
               COUNT(*)           AS donations
        FROM donations d
        JOIN campaigns c ON c.id = d.campaignId
        WHERE d.campaignId = %s AND c.createdBy = %s
        GROUP BY DATE(d.createdDate)
        ORDER BY day
        """,
        (campaign_id, fundraiser_id),
    )