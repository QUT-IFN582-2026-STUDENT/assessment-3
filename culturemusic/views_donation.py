from decimal import Decimal
from functools import wraps

import MySQLdb
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from . import db_donation
from . import models_donation
from .forms import DonationForm
from .models import AccountRole


bp_donation = Blueprint('bp_donation', __name__)

def supporter_required(view):
    """Restrict to authenticated and with supporter role."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in as a supporter to make donations.', 'error')
            return redirect(url_for('main.login'))
        if session.get('role') != AccountRole.SUPPORTER.value:
            flash('Only supporters can make donations.', 'error')
            return redirect(url_for('main.index'))
        return view(*args, **kwargs)
    return wrapped


@bp_donation.get('/donation/', defaults={'campaign_id': None})
@bp_donation.get('/donation/<int:campaign_id>/')
def donation(campaign_id):
    """ 
    Invoked when donation tab or view button in the home page is clicked.
    Param: campaign id or none
    Return: the selected campaign or the the top 1 active and featured campaign
    Render: donation page
    """
    if campaign_id is None:
        campaign_id = request.values.get('campaign_id', type=int)
    if (
        request.args.get('check') == 'supporter-required'
        and session.get('logged_in')
        and session.get('role') != AccountRole.SUPPORTER.value
    ):
        flash(
            'Please log out, then log in with a Supporter account to donate.',
            'error',
        )

    page = models_donation.get_donation_page(
        campaign_id,
        session.get('user_id') if session.get('logged_in') else None,
    )
 
    if page is None or page.campaign is None:
        abort(404)

    donation_form = DonationForm(prefix='donation')
    donation_form.support_level.choices = models_donation.get_tier_choices(page.campaign.tiers)

    # set the default donation amount to 1st tier
    if page.campaign.tiers:
        first_tier = page.campaign.tiers[0]
        donation_form.support_level.data = str(first_tier.id)
        donation_form.donation_amount.data = Decimal(str(first_tier.amount))

    return render_template(
        'donation.html',
        campaign=page.campaign,
        posts=page.posts,
        donations=page.donations,
        donation_form=donation_form,
        user=page.user,
    )


@bp_donation.post('/donation/<int:campaign_id>/submit/')
@supporter_required
def submit_donation(campaign_id):
    """
    Executed upon submission of donor form.
    Param: campaign id
    Render: donation page
    """
    account_id = session.get('user_id')
    if campaign_id is None or account_id is None:
        abort(404)

    donation_form = DonationForm(prefix='donation')
    tiers = db_donation.get_tiers_by_campaign(campaign_id)
    donation_form.support_level.choices = models_donation.get_tier_choices(tiers)

    donation_form.campaign_id.data = int(campaign_id)
    donation_form.account_id.data = int(account_id)

    if not donation_form.validate_on_submit():
        flash('Please check the form submitted.', 'error')
        return redirect(url_for('bp_donation.donation', campaign_id=campaign_id))

    # reset the donor tier based on the donation amount
    tier = models_donation.calculate_tier_by_amount(float(donation_form.donation_amount.data),tiers)
    donation_form.support_level.data = tier.id

    try:
        db_donation.add_donation(donation_form)
    except MySQLdb.Error:
        flash('Issue saving your donation. Please try again.', 'error')
        return redirect(url_for('bp_donation.donation', campaign_id=campaign_id))

    flash('Thank you for donating, we appreciate your support!')
    return redirect(url_for('bp_donation.donation', campaign_id=campaign_id))


@bp_donation.post('/posts/<int:post_id>/report/')
def report_post(post_id):
   #TODO - implement save
    return redirect(url_for(
        'bp_donation.donation',
        campaign_id=request.form.get('campaign_id', type=int),
    ))
