from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class OrganisationType(Enum):
    SUPPORTER = 'Supporter'
    FUNDRAISER = 'Fundraiser'
    ADMIN = 'Admin'

    def __str__(self):
        return self.value

    def find_by_value(value):
        for status in OrganisationType:
            if status.value == value:
                return status
        return OrganisationType.SUPPORTER


class AccountRole(Enum):
    SUPPORTER = 'Supporter'
    FUNDRAISER = 'Fundraiser'
    ADMIN = 'Admin'

    def __str__(self):
        return self.value
    
    def find_by_value(value):
        for status in AccountRole:
            if status.value == value:
                return status
        return AccountRole.SUPPORTER


class AccountStatus(Enum):
    ACTIVE = 'Active'
    SUSPENDED = 'Suspended'
    CLOSED = 'Closed'

    def __str__(self):
        return self.value


class CampaignStatus(Enum):
    PENDING = 'Pending'
    ACTIVE = 'Active'
    PAUSED = 'Paused'
    DRAFT = 'Draft'
    CLOSED = 'Closed'
    REJECTED = 'Rejected'
    SUSPENDED = 'Suspended'

    def __str__(self):
        return self.value


class CampaignEventType(Enum):
    FREE = 'Free'
    TICKETED = 'Ticketed'

    def __str__(self):
        return self.value


class ReportType(Enum):
    MISLEADING_INFORMATION = 'Misleading information'
    INAPPROPRIATE_CONTENT = 'Inappropriate content'
    SPAM = 'Spam'
    FAKE_NEWS = 'Fake News'
    OTHER = 'Other'

    def __str__(self):
        return self.value


class ReportStatus(Enum):
    FOR_REVIEW = 'For Review'
    ACTION_TAKEN = 'Action Taken'
    NO_ACTION = 'No Action'

    def __str__(self):
        return self.value


class DonationPaymentType(Enum):
    CREDIT_CARD = 'Credit Card'
    PAYPAL = 'Paypal'
    GOOGLE_PAY = 'Google Pay'

    def __str__(self):
        return self.value


@dataclass
class Organisation:
    id: int
    name: str
    org_type: OrganisationType = OrganisationType.SUPPORTER
    description: str = ''
    logo_url: str = ''


@dataclass
class UserInfo:
    id: int = 0
    username: str = ''
    firstname: str = ''
    lastname: str = ''
    name: str = ''
    email: str = ''
    phone: str = ''
    password_hash: str = ''
    role: AccountRole = AccountRole.SUPPORTER
    account_status: AccountStatus = AccountStatus.ACTIVE
    organisation: Optional['Organisation'] = None
    created_at: str = ''
    amount: float = 0
    message: str = ''


@dataclass
class Tier:
    id: int
    name: str
    amount: float
    campaign: Optional['Campaign'] = None
    benefits: str = ''


@dataclass
class Campaign:
    id: int
    title: str
    organisation: Organisation
    goal_amount: float
    amount_raised: float = 0
    status: CampaignStatus = CampaignStatus.PENDING 
    location: str = ''
    event_date: str = ''
    event_start_time: str = ''
    event_end_time: str = ''
    overview: str = ''
    description: str = ''
    banner_image_url: str = ''
    is_featured: bool = False
    created_by: Optional[UserInfo] = None
    created_date: str = ''
    updated_date: str = ''
    publish_date: str = ''
    event_type: CampaignEventType = CampaignEventType.FREE
    tiers: List[Tier] = field(default_factory=list)
    supporter_count: int = 0
    visitor_count: int = 0

    @property
    def progress_percentage(self):
        if self.goal_amount <= 0:
            return 0
        return min(100, round(self.amount_raised / self.goal_amount * 100))

    @property
    def event_time(self):
        return ' - '.join(
            value for value in (self.event_start_time, self.event_end_time) if value
        )


@dataclass
class Post:
    id: int
    title: str
    message: str
    campaign: Optional[Campaign] = None
    image_url: str = ''
    created_date: str = ''


@dataclass
class Donation:
    id: int
    amount: float
    account: Optional[UserInfo] = None
    campaign: Optional[Campaign] = None
    tier: Optional[Tier] = None
    notes: str = ''
    receipt_id: str = ''
    donor_name: str = ''
    email: str = ''
    phone: str = ''
    message: str = ''
    payment_type: DonationPaymentType = DonationPaymentType.CREDIT_CARD
    is_anonymous: bool = False
    created_date: str = ''


@dataclass
class Report:
    id: int
    post: Optional[Post] = None
    post_id: int = 0
    report_type: ReportType = ReportType.OTHER
    report_status: ReportStatus = ReportStatus.FOR_REVIEW
    created_date: str = ''
    reviewed_by: Optional[UserInfo] = None