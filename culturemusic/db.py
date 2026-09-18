
from .models import Campaign, Customer, Donation, Organisation, Post, Purchase, Report, Tier, UserAccount, UserInfo


Users = [
    UserAccount('admin', 'admin', 'foobar@mail.com', 
                UserInfo('1', 'Admin', 'User', 'foobar@mail.com', 
                         '1234567890')
    ),
]

ItalianCulturalGroup = Organisation(
    1,
    'Italian Cultural Group',
    'A community-led organisation promoting Italian culture and arts in Queensland.',
    'logo-cm200x84.png',
)

Campaigns = [
    Campaign(
        1,
        'Rinascita Sonora Night',
        50000.00,
        32500.00,
        'Active',
        'Brisbane Powerhouse, 119 Lamington Street, New Farm QLD 4005',
        '18 September 2026',
        '7:00 pm - 9:00 pm',
        'Italian Cultural Group is a community-led organisation promoting Italian culture and arts in Queensland. The Rinascita Sonora fundraiser will support a night of live performances celebrating the musical traditions of Italy and its diaspora.',
        'Funds will cover artist fees, accessible venue hire, equipment, and free community tickets so that local families can experience and share the music that makes Brisbane special.',
        'artesitalia-conductor-5157153_1920.jpg',
        ItalianCulturalGroup,
        [
            Tier(1, 'Bronze', 25, 'Name listed on donor wall.'),
            Tier(2, 'Silver', 100, 'Support one free community ticket, receive event updates and name listed on donor wall.'),
            Tier(3, 'Gold', 250, 'Highlighted name on donor wall, acknowledgement in the event program and two event tickets.'),
            Tier(4, 'Platinum', 500, 'Highlighted name on donor wall, receive sponsor recognition, and four event tickets.'),
        ],
        supporter_count=128,
        visitor_count=2846,
    )
]

Posts = [
    Post(1, 'Local artists confirmed', 'Six local artists have joined the programme and will perform at Rinascita Sonora.', 'pexels-violins-1838390_1920.jpg', '10 August 2026'),
    Post(2, 'Community rehearsal day', 'Performers and volunteers gathered to prepare the event and connect with the community.', 'yannazazu-orchestra-2098877_1920.jpg', '23 August 2026'),
]

Customers = [
    Customer('Amelia F.', 200, 'Keep the music playing!'),
    Customer('Anonymous Supporter', 100, 'For our community artists.'),
    Customer('Daniel K.', 50, 'Can\'t wait for the festival.'),
    Customer('Sophia M.', 500, 'Celebrating Italian music and culture.'),
]

Donations = []
Purchases = []
Reports = []


def check_for_user(username, password):
    """Check if the username and password are valid."""
    for user in Users:
        # never store passwords in plain text in production code
        # this is just for demonstration purposes
        if user.username == username and user.password == password:
            return user
    return None  # or raise an exception if preferred

def add_user(form):
    """Add a new user."""
    Users.append(
        UserAccount(form.username.data, form.password.data, form.email.data,
            UserInfo(f'U{len(Users)}', 
                     form.firstname.data, form.surname.data , 
                     form.email.data, form.phone.data,
                     form.organisation.data
                    )
        )
    )


def get_campaign(campaign_id=1):
    return next((campaign for campaign in Campaigns if campaign.id == int(campaign_id)), Campaigns[0])


def get_posts(campaign_id=1):
    return Posts


def get_customers(campaign_id=1):
    return Customers


def add_donation(donation):
    Donations.append(donation)
    campaign = get_campaign()
    campaign.amount_raised += donation.amount
    campaign.supporter_count += 1
    Customers.insert(0, Customer(donation.donor_name if not donation.is_anonymous else 'Anonymous Supporter', donation.amount, donation.message))


def add_purchase(purchase):
    Purchases.append(purchase)


def add_report(report):
    Reports.append(report)
