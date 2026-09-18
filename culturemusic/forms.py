from flask_wtf import FlaskForm
from wtforms.fields import BooleanField, IntegerField, SelectField, SubmitField, StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, NumberRange, Optional, email


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
    # Organisation selection field with predefined choices: (id,name)
    organisation = SelectField(
        "Organisation",
        choices=[
            ("1", "Italian Cultural Group"),
            ("2", "Pacific Arts Collective"),
            ("3", "Pamana Filipino in Brisbane"),
        ],
        validators=[InputRequired()],
    )
    submit = SubmitField("Make Account")



class DonationForm(FlaskForm):
    donor_name = StringField('Full name', validators=[Optional()])
    donor_email = StringField('Email address', validators=[InputRequired(), email()])
    donor_phone = StringField('Phone number', validators=[Optional()])
    donation_amount = IntegerField('Donation amount (AUD)', validators=[InputRequired(), NumberRange(min=1)])
    support_level = SelectField('Donor tier', choices=[], validators=[InputRequired()])
    donor_message = TextAreaField('Message', validators=[Optional()])
    anonymous_donation = BooleanField('Make my donation anonymous')
    campaign_updates = BooleanField('Email me campaign updates')
    donation_payment = SelectField('Payment Method', choices=[('Credit Card', 'Credit Card'), ('PayPal', 'PayPal'), ('Google Pay', 'Google Pay')], validators=[InputRequired()])
    submit = SubmitField('Submit Donation')


class TicketForm(FlaskForm):
    ticket_name = StringField('Full name', validators=[InputRequired()])
    ticket_email = StringField('Email address', validators=[InputRequired(), email()])
    ticket_phone = StringField('Phone number', validators=[Optional()])
    attendees = IntegerField('Number of attendees', default=1, validators=[InputRequired(), NumberRange(min=1)])
    ticket_payment = SelectField('Method of payment', choices=[('Credit Card', 'Credit Card'), ('PayPal', 'PayPal'), ('Google Pay', 'Google Pay')], validators=[InputRequired()])
    submit = SubmitField('Reserve Tickets')

class ReportForm(FlaskForm):
    report_type = SelectField('Report type', choices=[('Misleading information', 'Misleading information'), ('Inappropriate content', 'Inappropriate content'), ('Spam', 'Spam'), ('Other', 'Other')], validators=[InputRequired()])
    submit = SubmitField('Submit report')


