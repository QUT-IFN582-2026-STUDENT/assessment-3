from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from . import db_donation
from . import models_donation
from .forms import DonationForm
from .models import AccountRole, Report, ReportType


bp_donation = Blueprint('bp_donation', __name__)


# Access control
def supporter_required(view):
    """Only an authenticated user may open the decorated endpoint."""
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
    if campaign_id is None:
        campaign_id = request.values.get('campaign_id', type=int)
    if (
        request.args.get('notice') == 'supporter-required'
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
    if page is None:
        abort(404)

    donation_form = DonationForm(prefix='donation')
    donation_form.support_level.choices = models_donation.get_tier_choices(
        page.campaign
    )

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
    campaign = models_donation.get_campaign(campaign_id)
    if campaign is None:
        abort(404)

    donation_form = DonationForm(prefix='donation')
    donation_form.support_level.choices = models_donation.get_tier_choices(campaign)
    if not donation_form.validate_on_submit():
        flash('Please check the submitted details.', 'error')
        return redirect(url_for('bp_donation.donation', campaign_id=campaign.id))

    try:
        models_donation.submit_donation(
            campaign=campaign,
            account_id=session.get('user_id'),
            amount=donation_form.donation_amount.data,
            tier_id=donation_form.support_level.data,
            notes=donation_form.donor_message.data or '',
            payment_value=donation_form.donation_payment.data,
            is_anonymous=donation_form.anonymous_donation.data,
        )
    except ValueError as error:
        flash(str(error), 'error')
        return redirect(url_for('bp_donation.donation', campaign_id=campaign.id))

    flash(f'Thank you for supporting {campaign.title}!')
    return redirect(url_for('bp_donation.donation', campaign_id=campaign.id))


@bp_donation.post('/posts/<int:post_id>/report/')
def report_post(post_id):
    
    return redirect(url_for(
        'bp_donation.donation',
        campaign_id=request.form.get('campaign_id', type=int),
    ))
