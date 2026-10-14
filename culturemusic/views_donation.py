from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from . import db_donation
from . import models_donation
from .forms import DonationForm
from .models import Report, ReportType


bp_donation = Blueprint('bp_donation', __name__)


# Access control
def authenticated_required(view):
    """Only an authenticated user may open the decorated endpoint."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in to donate to campaigns.', 'error')
            return redirect(url_for('main.login'))
        return view(*args, **kwargs)
    return wrapped



@bp_donation.get('/donation/', defaults={'campaign_id': None})
@bp_donation.get('/donation/<int:campaign_id>/')
def donation(campaign_id=None):
    if campaign_id is None:
        campaign_id = request.values.get('campaign_id', type=int)
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
@authenticated_required
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
    try:
        report_type = ReportType(request.form.get('report-type', ReportType.OTHER.value))
    except ValueError:
        flash('Please select a valid report type.', 'error')
        return redirect(url_for(
            'bp_donation.donation',
            campaign_id=request.form.get('campaign_id', type=int),
        ))
    db_donation.add_report(Report(
        id=db_donation.next_report_id(),
        post_id=post_id,
        report_type=report_type,
    ))
    flash('Thank you. The post has been reported for review.')
    return redirect(url_for(
        'bp_donation.donation',
        campaign_id=request.form.get('campaign_id', type=int),
    ))
