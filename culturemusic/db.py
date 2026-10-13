from hashlib import sha256
from hmac import compare_digest
from secrets import token_hex, token_urlsafe
from datetime import date, datetime
from typing import Any

from werkzeug.security import check_password_hash

from . import database
from .models import Campaign, CampaignStatus, Organisation, Post, Tier, UserInfo


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
