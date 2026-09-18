from dataclasses import dataclass, field
from typing import List


@dataclass
class UserInfo:
    id: str
    firstname: str
    surname: str
    email: str
    phone: str
    organisation: str = ''


@dataclass
class UserAccount:
    username: str
    password: str
    email: str
    info: UserInfo


@dataclass
class Organisation:
    id: int
    name: str
    description: str
    logo_url: str = ''


@dataclass
class Tier:
    id: int
    name: str
    amount: float
    benefits: str


@dataclass
class Campaign:
    id: int
    title: str
    goal_amount: float
    amount_raised: float
    status: str
    location: str
    event_date: str
    event_time: str
    overview: str
    description: str
    banner_image_url: str
    organisation: Organisation
    tiers: List[Tier] = field(default_factory=list)
    supporter_count: int = 0
    visitor_count: int = 0

    @property
    def progress_percentage(self):
        if self.goal_amount <= 0:
            return 0
        return min(100, round(self.amount_raised / self.goal_amount * 100))


@dataclass
class Post:
    id: int
    title: str
    message: str
    image_url: str
    created_date: str


@dataclass
class Customer:
    name: str
    amount: float
    message: str


@dataclass
class Donation:
    id: int
    amount: float
    donor_name: str
    email: str
    phone: str
    message: str
    tier: str
    payment_type: str
    is_anonymous: bool = False


@dataclass
class Purchase:
    id: int
    name: str
    email: str
    phone: str
    ticket_cost: float
    attendees: int
    payment_type: str

    @property
    def total_cost(self):
        return self.ticket_cost * self.attendees


@dataclass
class Report:
    id: int
    post_id: int
    report_type: str
    status: str = 'ForReview'