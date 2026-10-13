from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from .db import (
    account_exists,
    add_donation,
    add_report,
    add_user,
    check_for_user,
    get_account,
    get_campaign,
    get_customers,
    get_organisations,
    get_post_campaign_id,
    get_posts,
    hash_password,
)
from .forms import DonationForm, LoginForm, RegisterForm, ReportForm

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/campaign/')
def campaign():
    return render_template('campaign.html')


@bp.route('/admin/')
def admin():
    return render_template('admin_dashboard.html')


@bp.route('/donation/', defaults={'campaign_id': None}, methods=['GET', 'POST'])
@bp.route('/donation/<int:campaign_id>/', methods=['GET', 'POST'])
def donation(campaign_id):
    campaign = get_campaign(campaign_id)
    if campaign is None:
        abort(404)

    current_account = None
    account_id = session.get('account_id')
    if account_id is not None:
        current_account = get_account(int(account_id))
        if current_account is None:
            session.clear()

    donation_form = DonationForm(prefix='donation')
    donation_form.support_level.choices = [
        (str(tier.id), f'{tier.name} - ${tier.amount:,.0f}')
        for tier in campaign.tiers
    ]
    report_form = ReportForm()
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'donation' and current_account is None:
            return redirect(url_for('main.login'))

        if form_type == 'donation' and donation_form.validate_on_submit():
            tier = next(
                tier for tier in campaign.tiers
                if str(tier.id) == donation_form.support_level.data
            )
            add_donation(
                current_account['id'],
                campaign.id,
                tier.id,
                donation_form.donation_amount.data,
                donation_form.donor_message.data or '',
                donation_form.donation_payment.data,
                donation_form.anonymous_donation.data,
            )
            flash(
                'Your donation details were saved. Payment processing is not '
                'configured yet.'
            )
            return redirect(url_for('main.donation', campaign_id=campaign.id))
        flash('Please check the submitted details.', 'error')

    return render_template(
        'donation.html',
        campaign=campaign,
        posts=get_posts(campaign.id),
        supporters=get_customers(campaign.id),
        donation_form=donation_form,
        report_form=report_form,
        current_account=current_account,
        show_donation_form=request.args.get('show_form') == '1',
    )


@bp.post('/posts/<int:post_id>/report/')
def report_post(post_id):
    campaign_id = get_post_campaign_id(post_id)
    if campaign_id is None:
        abort(404)

    form = ReportForm()
    if form.validate_on_submit():
        add_report(post_id, form.report_type.data)
        flash('Thank you. The post has been reported for review.')
    else:
        flash('Please select a valid report reason.', 'error')
    return redirect(url_for('main.donation', campaign_id=campaign_id))


@bp.route('/register/', methods = ['POST', 'GET'])
def register():
    form = RegisterForm()
    organisations = get_organisations()
    form.organisation.choices = [('', 'No organisation')] + [
        (str(organisation['id']), organisation['name'])
        for organisation in organisations
    ]

    if request.method == 'POST':
        if form.validate_on_submit():
            if account_exists(form.username.data, form.email.data):
                flash('User already exists', 'error')
                return render_template('register.html', form=form)

            organisation_id = (
                int(form.organisation.data) if form.organisation.data else None
            )
            account_id = add_user(
                form.username.data,
                form.firstname.data,
                form.surname.data,
                form.email.data,
                form.phone.data,
                hash_password(form.password.data),
                organisation_id,
            )
            session.clear()
            session['account_id'] = account_id
            session['username'] = form.username.data
            session['logged_in'] = True
            flash('Registration successful!')
            return redirect(url_for('main.index'))

    return render_template('register.html', form=form)

@bp.route('/login/', methods = ['POST', 'GET'])
def login():
    form = LoginForm()

    if request.method == 'POST' and form.validate_on_submit():
        account = check_for_user(form.username.data, form.password.data)
        if account is None:
            flash('Invalid username or password', 'error')
        else:
            session.clear()
            session['account_id'] = account['id']
            session['username'] = account['username']
            session['logged_in'] = True
            flash('Login successful!')
            return redirect(url_for('main.index'))

    return render_template('login.html', form=form)
