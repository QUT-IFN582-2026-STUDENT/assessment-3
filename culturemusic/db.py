from datetime import date, datetime
from .models import (
    Campaign, CampaignStatusEnum, Customer, Donation, Organisation, Post,
    Purchase, Report, Tier, UserAccount, UserInfo,
)
from hashlib import sha256
from hmac import compare_digest
from secrets import token_hex, token_urlsafe
from datetime import date, datetime
from typing import Any

from werkzeug.security import check_password_hash

from . import database
from .models import Campaign, CampaignStatus, Organisation, Post, Tier, UserInfo

Users = [
    UserAccount('admin', 'admin', 'foobar@mail.com',
                UserInfo('1', 'Admin', 'User', 'foobar@mail.com', '1234567890'),
                role='admin'),
]

ItalianCulturalGroup = Organisation(
    1,
    'Italian Cultural Group',
    'A community-led organisation promoting Italian culture and arts in Queensland.',
    'logo-cm200x84.png',
)

_admin_account = Users[0]

Campaigns = [
    Campaign.createDraft(
        id=1,
        title='Rinascita Sonora Night',
        goal_amount=50000.00,
        location='Brisbane Powerhouse, 119 Lamington Street, New Farm QLD 4005',
        event_date=date(2026, 9, 18),
        event_start_time=datetime(2026, 9, 18, 19, 0),
        event_end_time=datetime(2026, 9, 18, 21, 0),
        overview='Italian Cultural Group is a community-led organisation promoting Italian culture and arts in Queensland. The Rinascita Sonora fundraiser will support a night of live performances celebrating the musical traditions of Italy and its diaspora.',
        description='Funds will cover artist fees, accessible venue hire, equipment, and free community tickets so that local families can experience and share the music that makes Brisbane special.',
        created_by=_admin_account,
        organisation=ItalianCulturalGroup,
        banner_image_url='artesitalia-conductor-5157153_1920.jpg',
        tiers=[
            Tier(1, 'Bronze', 25, 'Name listed on donor wall.'),
            Tier(2, 'Silver', 100, 'Support one free community ticket, receive event updates and name listed on donor wall.'),
            Tier(3, 'Gold', 250, 'Highlighted name on donor wall, acknowledgement in the event program and two event tickets.'),
            Tier(4, 'Platinum', 500, 'Highlighted name on donor wall, receive sponsor recognition, and four event tickets.'),
        ],
    ),
]
# This sample campaign is Active with supporters already, so promote it past Draft:
Campaigns[0].changeStatus(CampaignStatusEnum.ACTIVE, actor_role='admin')
Campaigns[0].supporter_count = 128
Campaigns[0].visitor_count = 2846
Campaigns[0].calculateAmountRaised([])  # placeholder; set directly below for sample data
Campaigns[0]._amount_raised = 32500.00

Posts = [
    Post(1, 'Local artists confirmed', 'Six local artists have joined the programme and will perform at Rinascita Sonora.', 'pexels-violins-1838390_1920.jpg', '10 August 2026'),
    Post(2, 'Community rehearsal day', 'Performers and volunteers gathered to prepare the event and connect with the community.', 'yannazazu-orchestra-2098877_1920.jpg', '23 August 2026'),
]

Customers = [
    Customer('Amelia F.', 200, 'Keep the music playing!'),
    Customer('Anonymous Supporter', 100, 'For our community artists.'),
    Customer('Daniel K.', 50, "Can't wait for the festival."),
    Customer('Sophia M.', 500, 'Celebrating Italian music and culture.'),
]

Donations = []
Purchases = []
Reports = []



def hash_password(password: str) -> str:
    salt = token_hex(16)
    digest = sha256(f'{salt}{password}'.encode('utf-8')).hexdigest()
    return f'sha256${salt}${digest}'


def _check_password(stored_hash: str, password: str) -> bool:
    if stored_hash.startswith('sha256$'):
        try:
            algorithm, salt, expected_digest = stored_hash.split('$', 2)
        except ValueError:
            return False
        if algorithm != 'sha256':
            return False
        actual_digest = sha256(f'{salt}{password}'.encode('utf-8')).hexdigest()
        return compare_digest(actual_digest, expected_digest)

    return check_password_hash(stored_hash, password)


def _fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor = database.connection.cursor()
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()


def _fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    cursor = database.connection.cursor()
    try:
        cursor.execute(query, params)
        return cursor.fetchone()
    finally:
        cursor.close()


def _display_date(value: date | datetime | None) -> str:
    return value.strftime('%d %B %Y') if value else ''


def _display_time(value: datetime | None) -> str:
    return value.strftime('%I:%M %p').lstrip('0').lower() if value else ''


def get_campaign(campaign_id: int | None = None) -> Campaign | None:
    if campaign_id is None:
        row = _fetch_one(
            """
            SELECT c.id
            FROM campaigns AS c
            WHERE c.status = 'Active'
            ORDER BY
                (SELECT COUNT(*) FROM donations AS d
                 WHERE d.campaignId = c.id) DESC,
                (SELECT COUNT(*) FROM posts AS p
                 WHERE p.campaignId = c.id) DESC,
                c.isFeatured DESC,
                c.publishDate DESC,
                c.id DESC
            LIMIT 1
            """
        )
        if row is None:
            return None
        campaign_id = row['id']

    row = _fetch_one(
        """
        SELECT c.id, c.title, c.goalAmount, c.amountRaised, c.status,
               c.location, c.eventDate, c.eventStartTime, c.eventEndTime,
               c.overview, c.description, c.bannerImageUrl, c.orgId,
               o.name AS organisation_name,
               o.description AS organisation_description,
               (SELECT COUNT(*) FROM donations AS d
                WHERE d.campaignId = c.id) AS supporter_count
        FROM campaigns AS c
        JOIN organisations AS o ON o.id = c.orgId
        WHERE c.id = %s
        """,
        (campaign_id,),
    )
    if row is None:
        return None

    tier_rows = _fetch_all(
        """
        SELECT id, name, amount, benefits
        FROM tiers
        WHERE campaignId = %s
        ORDER BY amount, id
        """,
        (campaign_id,),
    )
    tiers = [
        Tier(
            id=tier['id'],
            name=tier['name'],
            amount=float(tier['amount']),
            benefits=tier['benefits'],
        )
        for tier in tier_rows
    ]
    start_time = row['eventStartTime']
    end_time = row['eventEndTime']
    event_time = ' - '.join(
        value for value in (_display_time(start_time), _display_time(end_time)) if value
    )
    organisation = Organisation(
        id=row['orgId'],
        name=row['organisation_name'],
        description=row['organisation_description'] or '',
    )

    return Campaign(
        id=row['id'],
        title=row['title'],
        goal_amount=float(row['goalAmount']),
        amount_raised=float(row['amountRaised']),
        status=CampaignStatus(row['status']),
        location=row['location'],
        event_date=_display_date(row['eventDate']),
        event_start_time=_display_time(start_time) if start_time else '',
        event_end_time=_display_time(end_time) if end_time else '',
        overview=row['overview'],
        description=row['description'],
        banner_image_url=row['bannerImageUrl'] or '',
        organisation=organisation,
        tiers=tiers,
        supporter_count=row['supporter_count'],
    )


def get_posts(campaign_id: int) -> list[Post]:
    rows = _fetch_all(
        """
        SELECT id, title, message, image_path, createdDate
        FROM posts
        WHERE campaignId = %s
        ORDER BY createdDate DESC, id DESC
        """,
        (campaign_id,),
    )
    posts = []
    for row in rows:
        image_path = row['image_path'] or ''
        if image_path and not image_path.startswith('img/'):
            image_path = f'img/{image_path}'
        posts.append(
            Post(
                id=row['id'],
                title=row['title'],
                message=row['message'],
                image_url=image_path,
                created_date=_display_date(row['createdDate']),
            )
        )
    return posts


def get_customers(campaign_id: int) -> list[UserInfo]:
    rows = _fetch_all(
        """
        SELECT
            a.id,
            a.username,
            a.firstName AS first_name,
            a.lastName AS last_name,
            CASE
                WHEN d.isAnonymous = 1 THEN 'Anonymous Supporter'
                ELSE CONCAT(a.firstName, ' ', a.lastName)
            END AS name,
            a.email,
            a.phone,
            d.amount,
            d.notes AS message
        FROM donations AS d
        LEFT JOIN accounts AS a ON a.id = d.accountId
        WHERE d.campaignId = %s
        ORDER BY d.createdDate DESC, d.id DESC
        LIMIT 10
        """,
        (campaign_id,),
    )
    return [
        UserInfo(
            id=row['id'] or 0,
            username=row['username'] or '',
            firstname=row['first_name'] or '',
            lastname=row['last_name'] or '',
            name=row['name'] or '',
            email=row['email'] or '',
            phone=row['phone'] or '',
            amount=float(row['amount']),
            message=row['message'] or '',
        )
        for row in rows
    ]


def get_account(account_id: int) -> dict[str, Any] | None:
    return _fetch_one(
        """
        SELECT id, username, firstName AS first_name, lastName AS last_name,
               email, phone, orgId AS org_id, role, accountStatus AS account_status
        FROM accounts
        WHERE id = %s AND accountStatus = 'Active'
        """,
        (account_id,),
    )


def get_organisations() -> list[dict[str, Any]]:
    return _fetch_all(
        """
        SELECT id, name
        FROM organisations
        WHERE orgType = 'Supporter'
        ORDER BY name
        """
    )


def check_for_user(username, password):
    for user in Users:
        if user.username == username and user.password == password:
            return user
    return None


def add_user(form):
    Users.append(
        UserAccount(form.username.data, form.password.data, form.email.data,
            UserInfo(f'U{len(Users)}',
                     form.firstname.data, form.surname.data,
                     form.email.data, form.phone.data,
                     form.organisation.data),
            role='supporter',
        )
    )


def get_campaign(campaign_id=1):
    return next((c for c in Campaigns if c.id == int(campaign_id)), Campaigns[0])


def get_all_campaigns():
    return Campaigns


def get_campaigns_by_owner(username):
    return [c for c in Campaigns if c.created_by.username == username]


def add_campaign(campaign):
    Campaigns.append(campaign)
    return campaign


def update_campaign(campaign_id, **fields):
    campaign = get_campaign(campaign_id)
    campaign.update(**fields)
    return campaign


def update_campaign_status(campaign_id, status: CampaignStatusEnum, actor_role='fundraiser'):
    campaign = get_campaign(campaign_id)
    return campaign.changeStatus(status, actor_role=actor_role)


def set_featured(campaign_id, featured: bool):
    """Admin-only: directly flips is_featured on the campaign. There is no
    public setter on Campaign for this — only the admin dashboard route
    should call this db function."""
    campaign = get_campaign(campaign_id)
    campaign._is_featured = featured
    campaign._touch()
    return campaign


def get_posts(campaign_id=1):
    return Posts


def add_post(post):
    Posts.append(post)
    return post


def get_customers(campaign_id=1):
    return Customers


def get_donations(campaign_id=1):
    return Donations


def add_donation(donation):
    Donations.append(donation)
    campaign = get_campaign()
    campaign._amount_raised += donation.amount
    campaign.supporter_count += 1
    Customers.insert(0, Customer(
        donation.donor_name if not donation.is_anonymous else 'Anonymous Supporter',
        donation.amount, donation.message,
    ))


def add_purchase(purchase):
    Purchases.append(purchase)


def add_report(report):
    Reports.append(report)
def check_for_user(username: str, password: str) -> dict[str, Any] | None:
    account = _fetch_one(
        """
        SELECT id, username, password_hash, accountStatus
        FROM accounts
        WHERE username = %s
        """,
        (username,),
    )
    if (
        account is None
        or account['accountStatus'] != 'Active'
        or not _check_password(account['password_hash'], password)
    ):
        return None
    return account


def account_exists(username: str, email: str) -> bool:
    return (
        _fetch_one(
            'SELECT id FROM accounts WHERE username = %s OR email = %s LIMIT 1',
            (username, email),
        )
        is not None
    )


def add_user(
    username: str,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    password_hash: str,
    organisation_id: int | None,
) -> int:
    connection = database.connection
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO accounts
                (username, firstName, lastName, email, phone, password_hash,
                 role, accountStatus, orgId)
            VALUES (%s, %s, %s, %s, %s, %s, 'Supporter', 'Active', %s)
            """,
            (
                username,
                first_name,
                last_name,
                email,
                phone,
                password_hash,
                organisation_id,
            ),
        )
        account_id = cursor.lastrowid
        connection.commit()
        return account_id
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def add_donation(
    account_id: int,
    campaign_id: int,
    tier_id: int,
    amount: int,
    notes: str,
    payment_type: str,
    is_anonymous: bool,
) -> None:
    connection = database.connection
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO donations
                (notes, receiptId, paymentType, accountId, campaignId,
                 tierId, amount, isAnonymous)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                notes,
                f'RCP-{token_urlsafe(24)}',
                payment_type,
                account_id,
                campaign_id,
                tier_id,
                amount,
                is_anonymous,
            ),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def get_post_campaign_id(post_id: int) -> int | None:
    row = _fetch_one('SELECT campaignId FROM posts WHERE id = %s', (post_id,))
    return row['campaignId'] if row else None


def add_report(post_id: int, report_type: str) -> None:
    connection = database.connection
    cursor = connection.cursor()
    try:
        cursor.execute(
            'INSERT INTO reports (postId, reportType) VALUES (%s, %s)',
            (post_id, report_type),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
