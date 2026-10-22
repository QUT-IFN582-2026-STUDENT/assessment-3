from dataclasses import dataclass
from typing import List, Optional, Tuple
from . import db, db_donation, db_campaign
from .forms import DonationForm
from .models import (
    Campaign,
    Donation,
    Post,
    Tier,
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
        donations=db_donation.get_donations(campaign.id),
        user=user,
    )


def get_tier_choices(tiers: List[Tier]) -> List[Tuple[str, str]]:
    return [
        (str(tier.id), f"{tier.name} - ${tier.amount:,.0f}")
        for tier in tiers
    ]
