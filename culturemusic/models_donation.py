from dataclasses import dataclass
import uuid
from typing import List, Optional, Tuple

from . import db_donation
from .models import (
    Campaign,
    Donation,
    DonationPaymentType,
    Post,
    UserInfo,
)


@dataclass
class DonationPage:
    campaign: Campaign
    posts: List[Post]
    donations: List[Donation]
    user: Optional[UserInfo]


def get_campaign(campaign_id: Optional[int]) -> Optional[Campaign]:
    return db_donation.get_campaign(campaign_id)


def get_donation_page(campaign_id: Optional[int],account_id: Optional[int] = None,) -> Optional[DonationPage]:
    campaign = get_campaign(campaign_id)
    if campaign is None:
        return None

    user = (
        db_donation.get_account_info(account_id)
        if account_id is not None
        else None
    )
    return DonationPage(
        campaign=campaign,
        posts=db_donation.get_posts(campaign.id),
        donations=db_donation.get_donations(campaign.id, campaign),
        user=user,
    )


def get_tier_choices(campaign: Campaign) -> List[Tuple[str, str]]:
    return [
        (str(tier.id), f"{tier.name} - ${tier.amount:,.0f}")
        for tier in campaign.tiers
    ]


def submit_donation(
    campaign: Campaign,
    account_id,
    amount: int,
    tier_id: str,
    notes: str,
    payment_value: str,
    is_anonymous: bool,
) -> None:
    if account_id is None:
        raise ValueError('Your account could not be loaded. Please sign in again.')

    account = db_donation.get_account_info(account_id)
    if account is None:
        raise ValueError('Your account could not be loaded. Please sign in again.')

    tier = next(
        (tier for tier in campaign.tiers if str(tier.id) == tier_id),
        None,
    )
    if tier is None:
        raise ValueError('Please select a valid donor tier.')

    payment_types = {
        'Credit Card': DonationPaymentType.CREDIT_CARD,
        'PayPal': DonationPaymentType.PAYPAL,
        'Paypal': DonationPaymentType.PAYPAL,
        'Google Pay': DonationPaymentType.GOOGLE_PAY,
    }
    payment_type = payment_types.get(payment_value)
    if payment_type is None:
        raise ValueError('Please select a valid payment method.')

    db_donation.add_donation(Donation(
        id=0,
        amount=amount,
        account=account,
        campaign=campaign,
        tier=tier,
        notes=notes,
        receipt_id=uuid.uuid4().hex,
        payment_type=payment_type,
        is_anonymous=is_anonymous,
    ))
