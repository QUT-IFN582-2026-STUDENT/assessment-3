from flask_wtf import FlaskForm
from wtforms.fields import BooleanField, DateField, DecimalField, IntegerField, SelectField, SubmitField, StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, NumberRange, Optional, email

from .models import CampaignEventType


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
    donation_amount = IntegerField('Donation amount (AUD)', validators=[InputRequired(), NumberRange(min=1, max=99999999)])
    support_level = SelectField('Donor tier', choices=[], validators=[InputRequired()])
    donor_message = TextAreaField('Message', validators=[Optional()])
    anonymous_donation = BooleanField('Make my donation anonymous')
    donation_payment = SelectField('Payment Method', choices=[('Credit Card', 'Credit Card'), ('Paypal', 'PayPal'), ('Google Pay', 'Google Pay')], validators=[InputRequired()])
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
