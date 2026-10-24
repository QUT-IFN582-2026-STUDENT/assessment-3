import csv
import io
import os
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from urllib.parse import urlparse

from flask import Blueprint, render_template, request, session, flash, abort, current_app, Response
from flask import redirect, url_for
from werkzeug.utils import secure_filename
from . import db
from . import db_campaign as cm

from .models import AccountRole
from .forms import LoginForm, RegisterForm, CampaignForm, PostForm
from .forms import SearchForm  # New line for search feature


bp = Blueprint('main', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}



# Access control
def fundraiser_required(view):
    """Only an authenticated fundraiser may open the decorated page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in as a fundraiser to manage campaigns.', 'error')
            return redirect(url_for('main.login'))
        if session.get('role') != AccountRole.FUNDRAISER.value:
            flash('Only fundraisers can access campaign management.', 'error')
            return redirect(url_for('main.index'))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    """Only an authenticated admin may open the decorated page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in as an admin to manage campaigns.', 'error')
            return redirect(url_for('main.login'))
        if session.get('role') != 'Admin':
            flash('Only admins can access administrator management.', 'error')
            return redirect(url_for('main.index'))
        return view(*args, **kwargs)
    return wrapped


def _selected_admin_row_id(field_name, row_label):
    selected_ids = request.form.getlist(field_name)
    if len(selected_ids) != 1:
        flash(f'Select exactly one {row_label} using its checkbox.', 'error')
        return None
    try:
        return int(selected_ids[0])
    except ValueError:
        flash(f'The selected {row_label} is invalid.', 'error')
        return None


def save_image(file_storage, directory='img'):
    """Save an uploaded image and return its web path, or '' if there is none."""
    if not file_storage or not file_storage.filename:
        return ''
    filename = secure_filename(file_storage.filename)
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError('Images must be PNG, JPG, GIF or WebP files.')
    unique_name = f'{uuid.uuid4().hex}.{extension}'
    folder = os.path.join(current_app.static_folder, directory)
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, unique_name))
    return f'{directory}/{unique_name}'


def read_campaign_extras(prefix):
    
    def parse(name):
        raw = request.form.get(f'{prefix}-{name}', '').strip()
        if not raw:
            return None
        try:
            return datetime.strptime(raw, '%Y-%m-%dT%H:%M')
        except ValueError:
            raise ValueError('Please enter a valid event start and end time.')

    start = parse('event_start_time')
    end = parse('event_end_time')
    if start and end and end <= start:
        raise ValueError('The event must end after it starts.')

    return start, end


def check_campaign_lengths(form):
    """Match the Campaign UML column sizes so MySQL never rejects the insert."""
    limits = (('title', 200, 'Title'), ('location', 100, 'Location'),
              ('overview', 500, 'Overview'), ('description', 2000, 'Description'))
    for field, limit, label in limits:
        value = getattr(form, field).data or ''
        if len(value) > limit:
            raise ValueError(f'{label} must be {limit} characters or fewer.')


MAX_TIER_SLOTS = 10


def raw_tiers(prefix):
    """The tier inputs exactly as submitted, so a failed form can be shown again."""
    try:
        slots = min(max(int(request.form.get(f'{prefix}-tier_count', 4)), 1), MAX_TIER_SLOTS)
    except ValueError:
        slots = 4
    return [{
        'name': request.form.get(f'{prefix}-tier{n}_name', ''),
        'amount': request.form.get(f'{prefix}-tier{n}_amount', ''),
        'benefits': request.form.get(f'{prefix}-tier{n}_benefits', ''),
    } for n in range(1, slots + 1)]


def read_tiers(prefix):
    tiers = []
    seen = set()
    for number, row in enumerate(raw_tiers(prefix), start=1):
        name = row['name'].strip()
        amount_text = row['amount'].strip()
        benefits = row['benefits'].strip()
        if not (name or amount_text or benefits):
            continue                                  # unused slot

        if not name:
            raise ValueError(f'Tier level {number} needs a name.')
        if len(name) > 100:
            raise ValueError(f'Tier level {number}: the name must be 100 characters or fewer.')
        if name.lower() in seen:
            raise ValueError(f'Tier names must be different (“{name}” is used twice).')
        seen.add(name.lower())

        try:
            amount = Decimal(amount_text).quantize(Decimal('0.01'))
        except (InvalidOperation, ValueError):
            raise ValueError(f'Tier level {number} needs an amount, for example 25 or 25.50.')
        if amount <= 0 or amount > Decimal('99999999.99'):
            raise ValueError(f'Tier level {number}: the amount must be greater than 0.')

        if len(benefits) > 500:
            raise ValueError(f'Tier level {number}: benefits must be 500 characters or fewer.')

        tiers.append({'name': name, 'amount': amount, 'benefits': benefits})

    if not tiers:
        raise ValueError('Add at least one donor tier, for example Bronze at $20.')
    return tiers



# Home page
@bp.route('/')
@bp.route('/index/')
def index():
    campaigns = db.search_campaigns('','',) #search all active campaigns

    return render_template(
            'index.html',
            searched=True,
            campaigns=campaigns,
            search_form=SearchForm(),
    )
   


'''
*********************************************************************************
Search Functionality
MVC = Controller
Flow is:
1 - Receives the request once the user selects the "Search" button in the nav bar
2 - Checks the inputs with SearchForm (which are found in forms.py)
3 - Asks the model (db.search_campaigns found in db.py) for matching cmapaigns
4 - Then hands the results to views.py to display them

Importantly, this route has no SQL or html in it. Also, the criteria appear in
the URL, so a search can be bookmarked or refreshed.
'''
@bp.route('/search/')
def search():
    # Load the form with the values from the URL query string
    # request.args = values sent with GET (request.form would be POST data)
    search_form = SearchForm(request.args)

    # Start with "no results"so the page still works if the search validation fails
    campaigns = []

    # validate() - this is to check the rules which are declared in searchform
    # The rule is that the keyword is at most 200 characters in length, and the event_type is one of the allowed choices
    
    if search_form.validate():
        # This passes the two criteria to the Model, this returns a list of objects (models.py)
        # the "or ''" part turns a missing value (None, e.g. someone opens /search/ with nothing in the URL) into an empty string, and strip() removes the stray spaces
        campaigns = db.search_campaigns(
            (search_form.keyword.data or '').strip(),
            search_form.event_type.data or '',
        )

    # This passes everything the VIEW needs to index.html:
    #   searched - True, so index.html shows the Search Results section
    #   campaigns -the list of Campaign objects to display
    #   search_form - the criteria (for the summary line) and any errors
    return render_template(
        'index.html',
        searched=True,
        campaigns=campaigns,
        search_form=search_form,
    )



# Campaign management (fundraiser only)

@bp.route('/campaign/', methods=['GET', 'POST'])
@fundraiser_required
def campaign():
    user_id = session['user_id']

    campaigns = cm.get_owned_campaigns(user_id)          # only this fundraiser's campaigns

    selected_id = request.values.get('campaign_id', type=int)
    if selected_id is None and campaigns:
        selected_id = campaigns[0]['id']

    # The ownership check happens inside the SQL query. If the campaign exists but
    # belongs to someone else, this returns None, exactly like a missing campaign.
    selected = cm.get_campaign_for_owner(selected_id, user_id) if selected_id else None
    if selected_id and selected is None:
        abort(404)

    campaign_form = CampaignForm(prefix='campaign')   # edit the selected campaign
    new_form = CampaignForm(prefix='new')             # create a new campaign
    post_form = PostForm(prefix='post')

    # Status is changed through its own dropdown (admin rules apply), so it must not be a required field on the create / edit forms.
    for form in (campaign_form, new_form):
        if hasattr(form, 'status'):
            del form.status

    # Pre-fill the edit form on a normal page load
    if selected and request.method == 'GET':
        campaign_form.title.data = selected['title']
        campaign_form.overview.data = selected['overview']
        campaign_form.description.data = selected['description']
        campaign_form.location.data = selected['location']
        campaign_form.goal_amount.data = selected['goal_amount']
        campaign_form.event_date.data = selected['event_date']
        campaign_form.event_type.data = selected['event_type']

    form_type = request.form.get('form_type') if request.method == 'POST' else None

    # Create a new campaign (starts as 'pending' until an admin approves it)
    if form_type == 'create':
        if new_form.validate_on_submit():
            try:
                check_campaign_lengths(new_form)
                start, end = read_campaign_extras('new')
                tiers = read_tiers('new')
                banner = save_image(request.files.get('new-banner'), 'img')
            except ValueError as error:
                flash(str(error), 'error')
            else:
                new_id = cm.add_campaign(
                    user_id,
                    new_form.title.data,
                    new_form.overview.data,
                    new_form.description.data,
                    new_form.location.data,
                    new_form.goal_amount.data,
                    new_form.event_date.data,
                    event_start_time=start,
                    event_end_time=end,
                    event_type=new_form.event_type.data,
                    banner_image_url=banner or None,
                    tiers=tiers,
                )
                flash('Campaign created. It will go live once an administrator approves it.')
                return redirect(url_for('main.campaign', campaign_id=new_id))
        else:
            flash('Please check the new campaign details.', 'error')

    # Edit the selected campaign
    elif form_type == 'campaign' and selected:
        if campaign_form.validate_on_submit():
            try:
                check_campaign_lengths(campaign_form)
                start, end = read_campaign_extras('campaign')
                tiers = read_tiers('campaign')
                banner = save_image(request.files.get('campaign-banner'), 'img')
            except ValueError as error:
                flash(str(error), 'error')
            else:
                ok = cm.update_campaign(
                    selected['id'], user_id,
                    campaign_form.title.data,
                    campaign_form.overview.data,
                    campaign_form.description.data,
                    campaign_form.location.data,
                    campaign_form.goal_amount.data,
                    campaign_form.event_date.data,
                    event_start_time=start,
                    event_end_time=end,
                    event_type=campaign_form.event_type.data,
                    banner_image_url=banner or None,
                )
                if ok:
                    cm.replace_tiers(selected['id'], user_id, tiers)
                    flash('Campaign updated successfully!')
                else:
                    flash('Update failed.', 'error')
                return redirect(url_for('main.campaign', campaign_id=selected['id']))
        else:
            flash('Please check the submitted details.', 'error')

    # Change operational status (active / paused / closed only)
    elif form_type == 'status' and selected:
        requested = request.form.get('status', '')
        if requested not in cm.FUNDRAISER_STATUSES:
            flash('That status can only be set by an administrator.', 'error')
        elif cm.update_campaign_status(selected['id'], user_id, requested):
            flash(f'Campaign status updated to {requested}.')
        else:
            flash('This campaign is controlled by an administrator '
                  '(pending, rejected or suspended) and cannot be changed.', 'error')
        return redirect(url_for('main.campaign', campaign_id=selected['id']))

    # Publish a post / update (optional image)
    elif form_type == 'post' and selected:
        if post_form.validate_on_submit():
            try:
                image_path = save_image(request.files.get('post-image'))
            except ValueError as error:
                flash(str(error), 'error')
            else:
                cm.add_post(selected['id'], user_id,
                            post_form.title.data, post_form.message.data, image_path)
                flash('Update published!')
                return redirect(url_for('main.campaign', campaign_id=selected['id']))
        else:
            flash('Please check the submitted details.', 'error')

    # Edit an existing post
    elif form_type == 'post_edit' and selected:
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        post_id = request.form.get('post_id', type=int)
        if not title or not message or len(title) > 150 or post_id is None:
            flash('A post needs a title (max 150 characters) and a message.', 'error')
        elif cm.update_post(post_id, user_id, title, message):
            flash('Post updated.')
        else:
            flash('Post not found.', 'error')
        return redirect(url_for('main.campaign', campaign_id=selected['id']))

    # Delete a post
    elif form_type == 'post_delete' and selected:
        post_id = request.form.get('post_id', type=int)
        if post_id is not None and cm.delete_post(post_id, user_id):
            flash('Post deleted.')
        else:
            flash('Post not found.', 'error')
        return redirect(url_for('main.campaign', campaign_id=selected['id']))

    # Delete the selected campaign (only if it has no donations)
    elif form_type == 'campaign_delete' and selected:
        if cm.delete_campaign(selected['id'], user_id):
            flash('Campaign deleted.')
            return redirect(url_for('main.campaign'))
        flash('Campaigns that have received donations cannot be deleted. '
              'Close the campaign instead.', 'error')
        return redirect(url_for('main.campaign', campaign_id=selected['id']))

    # A failed form is shown again with what the user typed in the tier boxes
    new_tiers_raw = raw_tiers('new') if form_type == 'create' else None
    edit_tiers_raw = raw_tiers('campaign') if form_type == 'campaign' else None

    return render_template(
        'campaign.html',
        campaigns=campaigns,
        tiers=cm.get_tiers(selected['id'], user_id) if selected else [],
        new_tiers_raw=new_tiers_raw,
        edit_tiers_raw=edit_tiers_raw,
        campaign=selected,
        posts=cm.get_posts(selected['id'], user_id) if selected else [],
        donations=cm.get_donations(selected['id'], user_id) if selected else [],
        stats=cm.get_campaign_stats(selected['id'], user_id) if selected else None,
        daily_totals=cm.get_donations_by_day(selected['id'], user_id) if selected else [],
        campaign_form=campaign_form,
        new_form=new_form,
        post_form=post_form,
        fundraiser_statuses=cm.FUNDRAISER_STATUSES,
        can_change_status=bool(selected and selected['status'] in cm.FUNDRAISER_STATUSES),
    )


def _csv_safe(value):
    """Stop spreadsheet programs from running a cell that starts like a formula."""
    text = '' if value is None else str(value)
    return "'" + text if text[:1] in ('=', '+', '-', '@') else text


@bp.route('/campaign/<int:campaign_id>/donations.csv')
@fundraiser_required
def export_donations(campaign_id):
    """Download the donation history of one of the fundraiser's own campaigns."""
    user_id = session['user_id']
    if cm.get_campaign_for_owner(campaign_id, user_id) is None:
        abort(404)

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['Donor', 'Amount', 'Tier', 'Date', 'Message'])
    for d in cm.get_donations(campaign_id, user_id):
        writer.writerow([
            _csv_safe('Anonymous Supporter' if d['is_anonymous'] else d['donor_name']),
            d['amount'],
            _csv_safe(d['tier_name']),
            d['created_at'].strftime('%Y-%m-%d'),
            _csv_safe(d['message']),
        ])
    return Response(
        out.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=campaign-{campaign_id}-donations.csv'},
    )




@bp.route('/admin/', methods=['GET', 'POST'])
@admin_required
def admin():

    user_id = session['user_id']

    is_admin = cm.check_admin() #Check if the user is a valid admin

    campaigns = cm.get_all_campaigns()         # only this admin's campaigns

    accounts = cm.get_all_accounts()         #Retrieve all accounts for admin view

    post_reports = cm.get_post_reports()  #Retrieve all post reports for admin view

    
    selected_id = request.values.get('campaign_id', type=int)

    campaign_selected = next((c for c in campaigns if c['id'] == selected_id), None) #Filter through the list of admin's campaigns

    campaign_form = CampaignForm(prefix='campaign') #Used to edit the pre filled campaign form

    #Prefill the edit form on the normal page load for campaigns
    if campaign_selected and request.method == 'GET':
        campaign_form.title.data = campaign_selected['title']
        campaign_form.overview.data = campaign_selected['overview']
        campaign_form.description.data = campaign_selected['description']
        campaign_form.location.data = campaign_selected['location']
        campaign_form.goal_amount.data = campaign_selected['goalAmount']
        campaign_form.event_date.data = campaign_selected['eventDate']
        
    
    form_type = request.form.get('form_type') if request.method == 'POST' else None

    if request.method == 'POST' and form_type == 'featured_campaigns':
        raw_featured_ids = request.form.getlist('featured_campaign_ids')
        try:
            selected_featured_ids = [int(campaign_id) for campaign_id in raw_featured_ids]
        except ValueError:
            flash('The featured campaign selection is invalid.', 'error')
            return redirect(url_for('main.admin'))

        campaign_ids = {campaign['id'] for campaign in campaigns}
        if any(campaign_id not in campaign_ids for campaign_id in selected_featured_ids):
            flash('One or more selected campaigns could not be found.', 'error')
            return redirect(url_for('main.admin'))

        cm.set_featured_campaigns(selected_featured_ids)
        flash('Featured campaigns updated successfully.', 'success')
        return redirect(url_for('main.admin'))

    if request.method == 'POST' and form_type == 'campaign_status':
        selected_campaign_id = _selected_admin_row_id('selected_campaign_ids', 'campaign')
        selected_campaign = next(
            (campaign for campaign in campaigns if campaign['id'] == selected_campaign_id),
            None,
        )
        requested_status = request.form.get('status', '').lower()
        allowed_from = cm.ADMIN_CAMPAIGN_STATUS_TRANSITIONS.get(requested_status)
        current_status = (
            selected_campaign.get('status', '').lower()
            if selected_campaign else ''
        )

        if selected_campaign_id is not None:
            if selected_campaign is None:
                flash('The selected campaign could not be found.', 'error')
            elif allowed_from is None:
                flash('That campaign status action is not allowed.', 'error')
            elif current_status not in allowed_from:
                flash('That status change is not valid for this campaign.', 'error')
            elif cm.admin_update_campaign_status(selected_campaign_id, requested_status):
                flash(f'Campaign status updated to {requested_status.title()}.', 'success')
            else:
                flash('The campaign status could not be updated.', 'error')

        return redirect(url_for(
            'main.admin',
            campaign_id=selected_campaign_id,
        ))

    # --- Edit the campaign as an admin ---
    if form_type == 'campaign' and campaign_selected:
        if campaign_form.validate_on_submit():
            try:
                check_campaign_lengths(campaign_form)
                start, end, event_type = read_campaign_extras('campaign')
            except ValueError as error:
                flash(str(error), 'error')
            else:
                ok = cm.update_campaign_as_admin(
                    campaign_selected['id'], user_id,
                    campaign_form.title.data,
                    campaign_form.overview.data,
                    campaign_form.description.data,
                    campaign_form.location.data,
                    campaign_form.goal_amount.data,
                    campaign_form.event_date.data,
                    event_start_time=start,
                    event_end_time=end,
                    event_type=event_type,
                )
                if ok:
                    flash('Campaign edited successfully!')
                    return redirect(url_for('main.admin', campaign_id=campaign_selected['id']))
                else:
                    flash('Update failed.', 'error')         
            flash('Please check the submitted details.', 'error')



    # --- Used to update the account status of a specific user ---
    if request.method =='POST' and form_type == 'account_status':
        selected_user_id = _selected_admin_row_id('selected_account_ids', 'account')
        requested_status = request.form.get('status', '')

        account_exists = any(account['id'] == selected_user_id for account in accounts)
        if selected_user_id is not None:
            if not account_exists:
                flash('The selected account could not be found.', 'error')
            elif requested_status not in cm.ACCOUNT_ALLOWED_STATUSES:
                flash('That status is not allowed.', 'error')
            elif cm.admin_update_account_status(selected_user_id, requested_status):
                flash(f'Account status updated to {requested_status.title()}.', 'success')
            else:
                flash('This account cannot be updated to this status.', 'error')

        return redirect(url_for('main.admin', user_id=selected_user_id))



    # --- Used to update the report status from a specific reported post ---
    if request.method == 'POST' and form_type == 'post_report_status':
        selected_report_id = _selected_admin_row_id('selected_report_ids', 'reported item')
        requested_status = request.form.get('status', '')
        report_exists = any(report['id'] == selected_report_id for report in post_reports)
        if selected_report_id is not None:
            if not report_exists:
                flash('The selected reported item could not be found.', 'error')
            elif requested_status not in cm.POST_REPORT_ALLOWED_STATUSES:
                flash('That status is not allowed.', 'error')
            elif cm.admin_update_post_report_status(selected_report_id, requested_status):
                flash(f'Report status updated to {requested_status}.', 'success')
            else:
                flash('This report cannot be updated to that status.', 'error')

        return redirect(url_for('main.admin'))
    

    return render_template('admin_dashboard.html', campaign_form=campaign_form,
                           campaigns = campaigns,
                           campaign_selected = campaign_selected,
                           campaign_status_actions=cm.ADMIN_CAMPAIGN_STATUS_ACTIONS,
                           is_admin = is_admin,
                           selected_id = selected_id,
                           can_change_status=True,
                           accounts = accounts,
                           user_id = user_id,
                           post_reports = post_reports,
                           )

# Authentication

@bp.route('/register/', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    organisations = db.get_organisations()
    form.organisation.choices = [
        ('', 'Select an organisation'),
        *((str(organisation.id), organisation.name) for organisation in organisations),
    ]
    if request.method == 'POST' and form.validate_on_submit():

        email = getattr(getattr(form, 'email', None), 'data', '') or ''

        # Check by username / email only, not by password
        if db.username_exists(form.username.data, email):
            flash('Username or email already registered', 'error')
            return redirect(url_for('main.register'))

        db.add_user(form)
        flash('Registration successful! Please log in.')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)


@bp.route('/login/', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if request.method == 'GET' and request.args.get('check') == 'not-login':
        flash('Please log in with a Supporter account to donate.', 'error')

    if request.method == 'POST' and form.validate_on_submit():

        user = db.check_for_user(form.username.data, form.password.data)
        if not user:
            flash('Invalid username or password', 'error')
            next_url = request.form.get('next')
            login_url = url_for('main.login', next=next_url) if next_url else url_for('main.login')
            return redirect(login_url)

        # Store identity and role in the (signed) session
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        role = AccountRole(user['role'])
        session['role'] = role.value
        session['logged_in'] = True
        flash('Login successful!')

        next_url = request.form.get('next', '')
        if next_url.startswith('/') and not next_url.startswith('//'):
            parsed_next = urlparse(next_url)
            if not parsed_next.scheme and not parsed_next.netloc:
                return redirect(next_url)
        if role is AccountRole.FUNDRAISER:
            return redirect(url_for('main.campaign'))
        return redirect(url_for('main.index'))

    return render_template('login.html', form=form)


@bp.route('/logout/')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))