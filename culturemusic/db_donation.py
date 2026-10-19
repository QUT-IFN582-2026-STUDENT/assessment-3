from typing import Optional

import MySQLdb

from . import db, db_campaign, mysql
from .models import (
    Campaign,
    Donation,
    DonationPaymentType,
    Post,
    Report,
    Tier,
    UserInfo,
)

_reports: list[Report] = []


def get_posts(campaign_id) -> list[Post]:
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            """
            SELECT id, title, message, image_path, createdDate
            FROM posts
            WHERE campaignId = %s
            ORDER BY createdDate DESC, id DESC
            """,
            (campaign_id,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

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


def get_donations(campaign_id, campaign: Campaign) -> list[Donation]:
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
            LEFT JOIN accounts a ON a.id = d.accountId
            LEFT JOIN organisations o ON o.id = a.orgId
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
            campaign=campaign,
            tier=tier,
            notes=row['notes'] or '',
            receipt_id=row['receiptId'],
            payment_type=DonationPaymentType(row['paymentType']),
            is_anonymous=bool(row['isAnonymous']),
            created_date=str(row['createdDate']),
        ))
    return donations


def add_donation(donation: Donation) -> int:
    if donation.campaign is None or donation.tier is None:
        raise ValueError('A donation must be linked to a campaign and tier.')
    account_id = int(donation.account.id) if donation.account else None
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
                donation.notes,
                donation.receipt_id,
                donation.payment_type.value,
                account_id,
                donation.campaign.id,
                donation.tier.id,
                donation.amount,
                donation.is_anonymous,
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


def next_report_id() -> int:
    return len(_reports) + 1


def add_report(report: Report) -> None:
    _reports.append(report)