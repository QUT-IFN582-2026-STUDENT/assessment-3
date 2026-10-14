from datetime import date, datetime
from . import mysql
import MySQLdb
from .models import (
    AccountRole, AccountStatus, Campaign, CampaignStatusEnum, Organisation, Tier,
    UserAccount, UserInfo,
)
from werkzeug.security import check_password_hash, generate_password_hash


def add_user(form):
    """Create an account from validated registration form data."""
    role = AccountRole.SUPPORTER
    organisation_id = int(form.organisation.data)
    if organisation_id != 4:
        role = AccountRole.FUNDRAISER

    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO accounts
                (username, password_hash, email, firstName, surName, phone, role, orgId)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                form.username.data,
                generate_password_hash(form.password.data),
                form.email.data,
                form.firstname.data,
                form.surname.data,
                form.phone.data,
                role.value,
                organisation_id,
            ),
        )
        mysql.connection.commit()
    except MySQLdb.Error:
        mysql.connection.rollback()
        raise
    finally:
        cursor.close()


def username_exists(username, email):
    """Check by username/email only for the already-registered test."""
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            'SELECT 1 AS found FROM accounts WHERE username = %s OR email = %s',
            (username, email),
        )
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def check_for_user(username, password):
    """Return the account dict if credentials are valid, otherwise None."""
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            'SELECT * FROM accounts WHERE username = %s',
            (username,),
        )
        user = cursor.fetchone()
    finally:
        cursor.close()

    if user and check_password_hash(user['password_hash'], password):
        return user
    return None


def _user_info_from_row(row, prefix='account'):
    account_id = row.get(f'{prefix}_id')
    if account_id is None:
        return None

    organisation_id = row.get(f'{prefix}_org_id')
    organisation = None
    if organisation_id is not None:
        organisation = Organisation(
            id=organisation_id,
            name=row[f'{prefix}_org_name'],
            description=row.get(f'{prefix}_org_description') or '',
            logo_url='',
        )

    return UserInfo(
        id=str(account_id),
        firstname=row.get(f'{prefix}_firstname') or '',
        surname=row.get(f'{prefix}_surname') or '',
        email=row.get(f'{prefix}_email') or '',
        phone=row.get(f'{prefix}_phone') or '',
        organisation=organisation,
        account_status=AccountStatus(row[f'{prefix}_account_status']),
        role=AccountRole(row[f'{prefix}_role']),
        created_date=str(row.get(f'{prefix}_created_at') or ''),
    )


def get_account_info(account_id):
    """Load a registered account's UserInfo from the accounts table."""
    if account_id is None:
        return None

    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            """
            SELECT a.id AS account_id, a.firstName AS account_firstname,
                   a.surName AS account_surname, a.email AS account_email,
                   a.phone AS account_phone, a.role AS account_role,
                   a.accountStatus AS account_account_status,
                   a.created_at AS account_created_at,
                   o.id AS account_org_id, o.name AS account_org_name,
                   o.description AS account_org_description
            FROM accounts a
            LEFT JOIN organisations o ON o.id = a.orgId
            WHERE a.id = %s
            """,
            (account_id,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    return _user_info_from_row(row) if row else None


def get_organisations() -> list[Organisation]:
    """Return organisations available for account registration."""
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            """
            SELECT id, name, description
            FROM organisations
            WHERE LOWER(name) <> 'culture music'
            ORDER BY CASE WHEN LOWER(name) = 'not listed' THEN 1 ELSE 0 END,
                     name
            """
        )
        results = cursor.fetchall()
    finally:
        cursor.close()
    return [
        Organisation(
            id=row['id'],
            name=row['name'],
            description=row['description'] or '',
            logo_url='',
        )
        for row in results
    ]

Users = [
    UserAccount(
        username='admin',
        password='admin',
        info=UserInfo(
            id='1',
            firstname='Admin',
            surname='User',
            email='foobar@mail.com',
            phone='1234567890',
            role=AccountRole.ADMIN,
        ),
    ),
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
