from flask_wtf import FlaskForm
from wtforms.fields import BooleanField, DateField, DecimalField, HiddenField, SelectField, SubmitField, StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, NumberRange, Optional, email

from .models import CampaignEventType, DonationPaymentType


class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField("Username", validators = [InputRequired()])
    password = PasswordField("Password", validators = [InputRequired()])
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    """Form for user registry."""
    username = StringField("Username", validators = [InputRequired(message="Please enter a username.")])
    password = PasswordField("Password", validators = [InputRequired()])
    email = StringField("Email", validators = [InputRequired(), email()])
    firstname = StringField("Your first name", validators = [InputRequired()])
    surname = StringField("Your surname", validators = [InputRequired()])
    phone = StringField("Your phone number", validators = [InputRequired()])
    organisation = SelectField(
        "Organisation",
        choices=[("", "Select an organisation")],
        validators=[InputRequired(message="Please select an organisation.")],
    )
    submit = SubmitField("Make Account")

class DonationForm(FlaskForm):
    campaign_id = HiddenField()
    account_id = HiddenField()
    donation_amount = DecimalField(
        'Donation amount (AUD)',
        places=2,
        validators=[InputRequired(), NumberRange(min=1, max=99999999)],
    )
    support_level = SelectField('Donor tier', choices=[], validators=[InputRequired()])
    donor_message = TextAreaField('Message', validators=[Optional()])
    anonymous_donation = BooleanField('Make my donation anonymous')
    donation_payment = SelectField(
        'Payment Method',
        choices=[
            (payment_type.value, payment_type.value)
            for payment_type in DonationPaymentType
        ],
        validators=[InputRequired()],
    )

    submit = SubmitField('Submit Donation')



class ReportForm(FlaskForm):
    report_type = SelectField('Report type', choices=[('Misleading information', 'Misleading information'), ('Inappropriate content', 'Inappropriate content'), ('Spam', 'Spam'), ('Other', 'Other')], validators=[InputRequired()])
    submit = SubmitField('Submit report')

class CampaignForm(FlaskForm):
    title = StringField('Campaign title', validators=[InputRequired()])
    overview = TextAreaField('Overview', validators=[InputRequired()])
    description = TextAreaField('Description', validators=[InputRequired()])
    location = StringField('Location', validators=[InputRequired()])
    event_date = DateField('Event date', format='%Y-%m-%d', validators=[InputRequired()])
    event_time = StringField('Event time', validators=[Optional()])
    goal_amount = DecimalField(
        'Fundraising goal',
        places=2,
        validators=[InputRequired(), NumberRange(min=1, max=99999999.99)],
    )
    event_type = SelectField(
        'Event type',
        choices=[(event_type.name, event_type.value) for event_type in CampaignEventType],
        default=CampaignEventType.FREE.value,
        validators=[InputRequired()],
    )
#    status = SelectField('Campaign status', choices=[
#        ('Draft', 'Draft'), ('Pending', 'Pending'), ('Active', 'Active'),
#        ('Paused', 'Paused'), ('Suspended', 'Suspended')
#    ], validators=[InputRequired()])
    submit = SubmitField('Submit')
    
class PostForm(FlaskForm):
    title = StringField('Post title', validators=[InputRequired()])
    message = TextAreaField('Update message', validators=[InputRequired()])
    submit = SubmitField('Publish Update')


'''
********************************************************************************
Search functionality content
MVC = part of the Controller handling. The search route in views.py uses this 
SearchForm class to check the values that the user typed into the nav bar in index.html
The data comes from the browser and then goes to views.py search function

'''
from wtforms.validators import Length   # new import, used only by SearchForm


class SearchForm(FlaskForm):
    """Holds and validates the two search criteria: keyword and event type."""

    class Meta:
        # CSRF (cross-site request forgery) protection is for forms that CHANGE
        # data with POST. Search only READS data and is sent with GET, and the
        # nav bar form has no hidden CSRF token. If CSRF stayed on, validate()
        # would always fail with "The CSRF token is missing".
        csrf = False

    # Keyword box. Matched against the campaign TITLE only.
    # Optional() -> the box may be left empty (search by event type only).
    # Length(max=200) -> the title column is VARCHAR(200), so a longer keyword
    # could never match; rejects it with a clear message.
    keyword = StringField(
        'Keyword',
        validators=[Optional(), Length(max=200)],
    )

    # This is the Event type dropdown.
    # The choices are built from existing CampaignEventType dataclass which is found in 
    # models.py (Free, Ticketed are the options), so the allowed values always match the
    # eventType column in the database.
    # ('', 'All event types') allows for the no filter option.
    # The SelectField class automatically rejects any value that is not in the choices,
    # for example a hand-edited URL with event_type = Concert will fail validation.
    event_type = SelectField(
        'Event type',
        choices=[('', 'All event types')]
                + [(event_type.value, event_type.value) for event_type in CampaignEventType],
        validators=[Optional()],
    )

    submit = SubmitField('Search')
