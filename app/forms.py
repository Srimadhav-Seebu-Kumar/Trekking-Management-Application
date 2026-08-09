from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)

from app.models import DIFFICULTIES, TREK_STATUSES


class RegisterForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    contact = StringField("Contact Number", validators=[DataRequired(), Length(max=50)])
    role = SelectField(
        "Register As",
        choices=[("trekker", "Trekker (User)"), ("staff", "Trek Staff")],
        validators=[DataRequired()],
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class ProfileForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    contact = StringField("Contact Number", validators=[DataRequired(), Length(max=50)])
    password = PasswordField(
        "New Password (leave blank to keep current)", validators=[Optional(), Length(min=6)]
    )
    submit = SubmitField("Save Changes")


class TrekForm(FlaskForm):
    name = StringField("Trek Name", validators=[DataRequired(), Length(max=150)])
    location = StringField("Location", validators=[DataRequired(), Length(max=150)])
    difficulty = SelectField("Difficulty", choices=[(d, d) for d in DIFFICULTIES], validators=[DataRequired()])
    duration_days = IntegerField("Duration (days)", validators=[DataRequired(), NumberRange(min=1)])
    total_slots = IntegerField("Total Slots", validators=[DataRequired(), NumberRange(min=1)])
    status = SelectField("Status", choices=[(s, s) for s in TREK_STATUSES], validators=[DataRequired()])
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Save Trek")

    def validate_end_date(self, field):
        if self.start_date.data and field.data and field.data < self.start_date.data:
            raise ValidationError("End date cannot be before start date.")


class AssignStaffForm(FlaskForm):
    staff_id = SelectField("Assign Staff", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Assign")


class StaffTrekUpdateForm(FlaskForm):
    available_slots = IntegerField("Available Slots", validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField(
        "Trek Status", choices=[("Open", "Open"), ("Closed", "Closed"), ("Completed", "Completed")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update Trek")


class SearchForm(FlaskForm):
    class Meta:
        csrf = False

    q = StringField("Search", validators=[Optional(), Length(max=150)])
    submit = SubmitField("Search")
