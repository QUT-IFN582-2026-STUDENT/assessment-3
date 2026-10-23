import uuid
from typing import Optional

import MySQLdb
from .forms import DonationForm
from . import db, db_campaign, mysql
from .models import (
    Campaign,
    CampaignEventType,
    CampaignStatusEnum,
    Donation,
    DonationPaymentType,
    Organisation,
    Post,
    Tier,
)


def get_campaign(campaign_id: Optional[int]) -> Optional[Campaign]:
    condition = ' AND c.id = %s' if campaign_id is not None else ''
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            f"""
            SELECT
                c.id, c.title, c.goalAmount, c.amountRaised, c.status,
                c.location, c.eventDate, c.eventStartTime, c.eventEndTime,
                c.overview, c.description, c.bannerImageUrl, c.isFeatured,
                c.createdDate, c.updatedDate, c.publishDate, c.eventType,
                supporter_count.supporter_count,
                o.id AS org_id, o.name AS org_name,
                o.description AS org_description
            FROM campaigns c
            LEFT JOIN organisations o ON o.id = c.orgId
            LEFT JOIN (
                SELECT campaignId, COUNT(*) AS supporter_count
                FROM donations
                GROUP BY campaignId
            ) supporter_count ON supporter_count.campaignId = c.id
            WHERE c.status = 'Active' {condition}
            ORDER BY c.isFeatured DESC, c.eventDate ASC, c.id DESC
            """,
            (campaign_id,) if campaign_id is not None else (),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    if row is None:
        return None

    return Campaign(
        _id=row['id'],
        _title=row['title'],
        _goal_amount=float(row['goalAmount']),
        _amount_raised=float(row['amountRaised']),
        _status=CampaignStatusEnum(row['status']),
        _location=row['location'],
        _event_date=row['eventDate'],
        _event_start_time=row['eventStartTime'],
        _event_end_time=row['eventEndTime'],
        _overview=row['overview'],
        _description=row['description'],
        _banner_image_url=row['bannerImageUrl'] or '',
        _event_type=CampaignEventType(row['eventType']),
        _is_featured=bool(row['isFeatured']),
        _created_date=row['createdDate'],
        _updated_date=row['updatedDate'],
        _publish_date=row['publishDate'],
        supporter_count=int(row.get('supporter_count') or 0),
        _organisation=Organisation(
            id=row['org_id'],
            name=row['org_name'],
            description=row['org_description'] or '',
        ) if row['org_id'] is not None else None,
    )


def get_posts(campaign_id) -> list[Post]:
    rows = db_campaign.query(
        """
        SELECT id, title, message, image_path, createdDate
        FROM posts
        WHERE campaignId = %s
        ORDER BY createdDate DESC, id DESC
        """, (campaign_id,))
    return [
        Post(
            id=row['id'],
            title=row['title'],
            message=row['message'],
            image_url=row['image_path'] or '',
            created_date=str(row['createdDate']),
        )
        for row in rows
    ]

def get_donations(campaign_id: int) -> list[Donation]:   
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            """
            SELECT d.id, d.notes, d.receiptId, d.paymentType, d.accountId,
                   d.campaignId, d.tierId, d.amount, d.isAnonymous, d.createdDate,
                   t.name AS tier_name, t.amount AS tier_amount,
                   t.benefits AS tier_benefits,
                   a.id AS account_id, a.firstName AS account_firstname,
                   a.surName AS account_surname, a.email AS account_email,
                   a.phone AS account_phone, a.role AS account_role,
                   a.accountStatus AS account_account_status,
                   a.created_at AS account_created_at,
                   o.id AS account_org_id, o.name AS account_org_name,
                   o.description AS account_org_description
            FROM donations d
            INNER JOIN accounts a ON a.id = d.accountId
            INNER JOIN organisations o ON o.id = a.orgId
            LEFT JOIN tiers t ON t.id = d.tierId
            WHERE d.campaignId = %s
            ORDER BY d.createdDate DESC, d.id DESC
            LIMIT 10
            """,
            (campaign_id,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    donations = []
    for row in rows:
        tier = None
        if row['tierId'] is not None:
            tier = Tier(
                id=row['tierId'],
                name=row['tier_name'] or '',
                amount=float(row['tier_amount'] or 0),
                benefits=row['tier_benefits'] or '',
            )
        donations.append(Donation(
            id=row['id'],
            amount=float(row['amount']),
            account=db._user_info_from_row(row),
            tier=tier,
            campaign=None,  # Campaign object is not required.
            notes=row['notes'] or '',
            receipt_id=row['receiptId'],
            payment_type=DonationPaymentType(row['paymentType']),
            is_anonymous=bool(row['isAnonymous']),
            created_date=str(row['createdDate']),
        ))
    return donations


def add_donation(donation: DonationForm) -> int:
    """
    Save donation to database and return its id.
    """
   
    payment_type = DonationPaymentType(donation.donation_payment.data)
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO donations
                (notes, receiptId, paymentType, accountId, campaignId, tierId,
                 amount, isAnonymous)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                donation.donor_message.data or '',
                uuid.uuid4().hex,
                payment_type.value,
                int(donation.account_id.data),
                int(donation.campaign_id.data),
                int(donation.support_level.data),
                float(donation.donation_amount.data),
                bool(donation.anonymous_donation.data),
            ),
        )
        donation_id = cursor.lastrowid
        mysql.connection.commit()
        return donation_id
    except MySQLdb.Error:
        mysql.connection.rollback()
        raise
    finally:
        cursor.close()


def get_tiers_by_campaign(campaign_id: int) -> list[Tier]:
    rows =  db_campaign.query('SELECT id, name, amount, benefits FROM tiers WHERE campaignId = %s',(campaign_id,), one=False)
    return [
        Tier(
            id=row['id'],
            name=row['name'],
            amount=float(row['amount']),
            benefits=row['benefits'],
        )
        for row in rows
    ]
