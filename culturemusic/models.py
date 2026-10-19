from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

class CampaignStatusEnum(Enum):
    DRAFT = 'Draft'
    PENDING = 'Pending'
    ACTIVE = 'Active'
    PAUSED = 'Paused'
    SUSPENDED = 'Suspended'
    REJECTED = 'Rejected'
    CLOSED = 'Closed'

    def __str__(self):
        return self.value

class AccountRole(Enum):
    SUPPORTER = 'Supporter'
    FUNDRAISER = 'Fundraiser'
    ADMIN = 'Admin'

    def __str__(self):
        return self.value

class AccountStatus(Enum):
    ACTIVE = 'Active'
    SUSPENDED = 'Suspended'
    CLOSED = 'Closed'

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
    PAYPAL = 'PayPal'
    GOOGLE_PAY = 'Google Pay'

    def __str__(self):
        return self.value

    def find_by_value(value):
        for payment_type in DonationPaymentType:
            if payment_type.value == value:
                return payment_type
        return DonationPaymentType.CREDIT_CARD


@dataclass
class UserInfo:
    id: str
    firstname: str
    surname: str
    email: str
    phone: str
    organisation: Optional['Organisation'] = None
    account_status: AccountStatus = AccountStatus.ACTIVE
    role: AccountRole = AccountRole.SUPPORTER
    created_date: str = ''


@dataclass
class UserAccount:
    """Merged with the former 'Account' class used by Campaign.createdBy.
    role: 'admin' | 'fundraiser' | 'supporter'"""
    username: str
    password: str
    info: UserInfo



@dataclass
class Organisation:
    id: int
    name: str
    description: str
    logo_url: str


@dataclass
class Tier:
    id: int
    name: str
    amount: float
    campaign: Optional['Campaign'] = None
    benefits: str = ''


_FUNDRAISER_ALLOWED_TRANSITIONS = {
    CampaignStatusEnum.DRAFT:   {CampaignStatusEnum.PENDING},
    CampaignStatusEnum.ACTIVE:  {CampaignStatusEnum.PAUSED, CampaignStatusEnum.CLOSED},
    CampaignStatusEnum.PAUSED:  {CampaignStatusEnum.ACTIVE, CampaignStatusEnum.CLOSED},
}


@dataclass
class Campaign:
    _id: int
    _title: str
    _goal_amount: float
    _amount_raised: float
    _status: CampaignStatusEnum
    _location: str
    _event_date: date
    _event_start_time: datetime
    _event_end_time: datetime
    _overview: str
    _description: str
    _banner_image_url: str 
    _created_by: UserAccount
    _organisation: Organisation
    _event_type: CampaignEventType = CampaignEventType.FREE
    _is_featured: bool = False
    _tiers: List[Tier] = field(default_factory=list)
    _created_date: datetime = field(default_factory=datetime.now)
    _updated_date: datetime = field(default_factory=datetime.now)
    _publish_date: Optional[datetime] = None
    supporter_count: int = 0
    visitor_count: int = 0


    # ---- Properties ----

    @property
    def id(self) -> int:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value
        self._touch()

    @property
    def goal_amount(self) -> float:
        return self._goal_amount

    @goal_amount.setter
    def goal_amount(self, value: float) -> None:
        self._goal_amount = value
        self._touch()

    @property
    def amount_raised(self) -> float:
        return self._amount_raised

    @property
    def status(self) -> CampaignStatusEnum:
        return self._status

    @property
    def location(self) -> str:
        return self._location

    @location.setter
    def location(self, value: str) -> None:
        self._location = value
        self._touch()

    @property
    def event_date(self) -> date:
        return self._event_date

    @property
    def event_start_time(self) -> datetime:
        return self._event_start_time

    @property
    def event_end_time(self) -> datetime:
        return self._event_end_time

    @property
    def overview(self) -> str:
        return self._overview

    @overview.setter
    def overview(self, value: str) -> None:
        self._overview = value
        self._touch()

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value
        self._touch()

    @property
    def banner_image_url(self) -> str:
        return self._banner_image_url

    @banner_image_url.setter
    def banner_image_url(self, value: str) -> None:
        self._banner_image_url = value
        self._touch()

    @property
    def is_featured(self) -> bool:
        return self._is_featured
    # No public setter here on purpose: only the admin dashboard route may
    # flip this, and it does so via db.set_featured(), not via the model.

    @property
    def tiers(self) -> List[Tier]:
        return self._tiers

    @property
    def created_by(self) -> UserAccount:
        return self._created_by

    @property
    def organisation(self) -> Organisation:
        return self._organisation

    @property
    def event_type(self) -> CampaignEventType:
        return self._event_type

    @property
    def created_date(self) -> datetime:
        return self._created_date

    @property
    def updated_date(self) -> datetime:
        return self._updated_date

    @property
    def publish_date(self) -> Optional[datetime]:
        return self._publish_date

    @property
    def progress_percentage(self) -> int:
        if self._goal_amount <= 0:
            return 0
        return min(100, round(self._amount_raised / self._goal_amount * 100))

    # ---- Behaviours ----

    def calculateAmountRaised(self, donations: List['Donation'] = None) -> float:
        if donations is not None:
            self._amount_raised = sum(d.amount for d in donations)
        return self._amount_raised

    @classmethod
    def createDraft(
        cls,
        id: int,
        title: str,
        goal_amount: float,
        location: str,
        event_date: date,
        event_start_time: datetime,
        event_end_time: datetime,
        overview: str,
        description: str,
        created_by: UserAccount,
        organisation: Organisation,
        banner_image_url: str = '',
        event_type: str = '',
        tiers: List[Tier] = None,
    ) -> 'Campaign':
        return cls(
            _id=id,
            _title=title,
            _goal_amount=goal_amount,
            _amount_raised=0.0,
            _status=CampaignStatusEnum.DRAFT,
            _location=location,
            _event_date=event_date,
            _event_start_time=event_start_time,
            _event_end_time=event_end_time,
            _overview=overview,
            _description=description,
            _banner_image_url=banner_image_url,
            _created_by=created_by,
            _organisation=organisation,
            _event_type=event_type,
            _is_featured=False,
            _tiers=tiers or [],
        )

    def update(self, **fields) -> bool:
        editable = {
            'title', 'goal_amount', 'location', 'event_date', 'event_start_time',
            'event_end_time', 'overview', 'description', 'banner_image_url',
            'event_type', 'tiers',
        }
        for key, value in fields.items():
            if key not in editable:
                return False
            setattr(self, f'_{key}', value)
        self._touch()
        return True

    def changeStatus(self, status: CampaignStatusEnum, actor_role: str = 'fundraiser') -> bool:
        if actor_role == 'admin':
            self._status = status
            self._touch()
            return True
        allowed = _FUNDRAISER_ALLOWED_TRANSITIONS.get(self._status, set())
        if status not in allowed:
            return False
        self._status = status
        self._touch()
        return True

    def _touch(self) -> None:
        self._updated_date = datetime.now()

    @property
    def event_time(self):
        return ' - '.join(
            value.strftime('%I:%M %p').lstrip('0').lower()
            for value in (self.event_start_time, self.event_end_time)
            if value
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