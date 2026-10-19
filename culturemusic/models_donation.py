from dataclasses import dataclass
import uuid
from typing import List, Optional, Tuple
from . import db, db_donation, db_campaign
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


def get_donation_page(campaign_id: Optional[int],account_id: Optional[int] = None,) -> Optional[DonationPage]:
   
    campaign = db_campaign.get_public_campaign(campaign_id)
    
    if campaign is None:
        return None
    user = (
        db.get_account_info(account_id)
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
    amount: float,
    tier_id: str,
    notes: str,
    payment_value: str,
    is_anonymous: bool,
) -> None:
    
    account = db.get_account_info(account_id)
    tier = next(
        (tier for tier in campaign.tiers if str(tier.id) == tier_id),
        None,
    )
  
    payment_type = DonationPaymentType.find_by_value(payment_value) 
    
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
