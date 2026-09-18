from flask import Blueprint, render_template, request, session, flash
from flask import redirect, url_for

from .db import add_donation, add_purchase, add_report, get_campaign, get_customers, get_posts, check_for_user, add_user
from .models import Donation, Purchase, Report
from .forms import DonationForm, LoginForm, RegisterForm, TicketForm

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


@bp.route('/donation/', methods=['GET', 'POST'])
def donation():
    campaign = get_campaign()
    donation_form = DonationForm(prefix='donation')
    ticket_form = TicketForm(prefix='ticket')
    donation_form.support_level.choices = [
        (str(tier.id), f'{tier.name} - ${tier.amount:,.0f}')
        for tier in campaign.tiers
    ]

    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'donation' and donation_form.validate_on_submit():
            tier = next(tier for tier in campaign.tiers if str(tier.id) == donation_form.support_level.data)
            add_donation(Donation(
                len(get_customers()) + 1,
                donation_form.donation_amount.data,
                donation_form.donor_name.data or 'Anonymous Supporter',
                donation_form.donor_email.data,
                donation_form.donor_phone.data or '',
                donation_form.donor_message.data or '',
                tier.name,
                donation_form.donation_payment.data,
                donation_form.anonymous_donation.data,
            ))
            flash('Thank you for supporting Rinascita Sonora!')
            return redirect(url_for('main.donation'))
        if form_type == 'ticket' and ticket_form.validate_on_submit():
            add_purchase(Purchase(
                len(get_customers()) + 1,
                ticket_form.ticket_name.data,
                ticket_form.ticket_email.data,
                ticket_form.ticket_phone.data or '',
                50.00,
                ticket_form.attendees.data,
                ticket_form.ticket_payment.data,
            ))
            flash('Your tickets have been reserved!')
            return redirect(url_for('main.donation'))
        flash('Please check the submitted details.', 'error')

    return render_template(
        'donation.html',
        campaign=campaign,
        posts=get_posts(campaign.id),
        supporters=get_customers(campaign.id),
        donation_form=donation_form,
        ticket_form=ticket_form,
        ticket_cost=50.00,
    )


@bp.post('/posts/<int:post_id>/report/')
def report_post(post_id):
    report_type = request.form.get('report-type', 'Other')
    add_report(Report(len(get_customers()) + 1, post_id, report_type))
    flash('Thank you. The post has been reported for review.')
    return redirect(url_for('main.donation'))


@bp.route('/register/', methods = ['POST', 'GET'])
def register():
    form = RegisterForm()
    if request.method == 'POST':

        if form.validate_on_submit():

            # Check if the user already exists
            user = check_for_user(
                form.username.data, form.password.data
            )
            if user:
                flash('User already exists', 'error')
                return redirect(url_for('main.register'))

            # Store user information in the database
            add_user(
                form
            )
            flash('Registration successful!')
            return redirect(url_for('main.login'))

    return render_template('register.html', form = form)

@bp.route('/login/', methods = ['POST', 'GET'])
def login():
    form = LoginForm()
    if request.method == 'POST':

        if form.validate_on_submit():

            # Check if the user exists in the database
            user = check_for_user(
                form.username.data, form.password.data
            )
            if not user:
                flash('Invalid username or password', 'error')
                return redirect(url_for('main.login'))

            # Store user information in the session
            session['username'] = user.username
            session['logged_in'] = True
            flash('Login successful!')
            return redirect(url_for('main.index'))

    return render_template('login.html', form = form)
