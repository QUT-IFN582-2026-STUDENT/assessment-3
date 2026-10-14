from datetime import date, datetime
from .models import (
    Campaign, CampaignStatusEnum, Customer, Donation, Organisation, Post,
    Purchase, Report, Tier, UserAccount, UserInfo,
)


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