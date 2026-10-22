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


'''
**************************************************************************************
Search Functionality
MVC = Model

Everything that talks to the database lives in this .py.
The controller (views.py search route) calls the search_campaigns(), with the
view (index.html) only ever receiving the the final campaign objects as requested.
The html pages never see SQL directly and they never connect to the database, this is a big no-no.

'''


from .models import CampaignEventType   # new import


def search_campaigns(keyword, event_type):
    """
    This function finds public campaigns by the title keyword input and/or the event type dropdown selection

    This function is called by the views.py-search() route
    The function recieves  both the :
        keyword (text typed in the search box ('' = any title)), and 
        event_type ('Free', 'Ticketed', or '' (= any event type))
    
    The function returns a list of campaign dataclass objects (models.py), which are then passed back
    to the route, which then passes them to index.html

    """
    # SQL build
    # Only the 'Active' campaigns are made public. (Status = Pending, Paused, Suspended, Rejected.
    # The Draft and Closed campaigns will never appear in a public search function. 
    # The jons will fetch the organisation and the creating account, because the existing Campaign dataclass needs
    # an Organisation and a UserAccount.
    sql = """
        SELECT c.id, c.title, c.goalAmount, c.amountRaised, c.status,
               c.location, c.eventDate, c.eventStartTime, c.eventEndTime,
               c.overview, c.description, c.bannerImageUrl, c.isFeatured,
               c.eventType, c.createdDate, c.updatedDate, c.publishDate,
               o.id AS org_id, o.name AS org_name, o.description AS org_description,
               a.id AS creator_id, a.username AS creator_username,
               a.firstName AS creator_firstname, a.surName AS creator_surname,
               a.email AS creator_email, a.phone AS creator_phone
        FROM campaigns c
        JOIN organisations o ON o.id = c.orgId
        JOIN accounts a ON a.id = c.createdBy
        WHERE c.status = 'Active'
    """


    # Params Variable
    # The params variable will hold the values which are input by the user. 
    # They are sent to MySQL seperately from the SQL text (each %s is a placeholder).
    # MySQL treats them as plain data, never as SQL commands. 
    # This is what prevents SQL injection - very important
    params = []


    # Keyword filter (applies only if something was typed)
    # The database collation is case-insensitive
    if keyword:
        sql = sql + " AND c.title LIKE %s"
        params.append('%' + keyword + '%')

    # Event type filter (only if a type was chosen by the user in the dropdown)
    if event_type:
        sql = sql + " AND c.eventType = %s"
        params.append(event_type)

    # This specifies the soonest/closest event first
    sql = sql + " ORDER BY c.eventDate, c.title"

    # Run the query
    # Applies the same cursor pattern as the existing functions in this file
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(sql, params)
        rows = cursor.fetchall()     # list of dicts, one per campaign
    finally:
        cursor.close()

    # Dtabase rows turned into data classes
    # Organisation, UserInfo, UserAccount and Campaign all come from models.py
    campaigns = []
    for row in rows:
        organisation = Organisation(
            id=row['org_id'],
            name=row['org_name'],
            description=row['org_description'] or '',
            logo_url='',
        )
        creator = UserAccount(
            username=row['creator_username'],
            password='',  # never loads or passes a password to a page
            info=UserInfo(
                id=str(row['creator_id']),
                firstname=row['creator_firstname'],
                surname=row['creator_surname'],
                email=row['creator_email'],
                phone=row['creator_phone'] or '',
            ),
        )
        campaign = Campaign(
            _id=row['id'],
            _title=row['title'],
            _goal_amount=float(row['goalAmount']), # decimal to float
            _amount_raised=float(row['amountRaised']),
            _status=CampaignStatusEnum(row['status']),# 'Active' to enum
            _location=row['location'],
            _event_date=row['eventDate'],
            _event_start_time=row['eventStartTime'],
            _event_end_time=row['eventEndTime'],
            _overview=row['overview'],
            _description=row['description'],
            _banner_image_url=row['bannerImageUrl'] or '',
            _created_by=creator,
            _organisation=organisation,
            _event_type=CampaignEventType(row['eventType']),# 'Free' to enum
            _is_featured=bool(row['isFeatured']),
            _created_date=row['createdDate'],
            _updated_date=row['updatedDate'],
            _publish_date=row['publishDate'],
        )
        campaigns.append(campaign)

    return campaigns
