from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Optional


class LoginForm(FlaskForm):
    employee_id = StringField('ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    name = StringField('Full name', validators=[DataRequired()])
    employee_id = StringField('ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')
    department = StringField('Department', validators=[Optional()])
    section = StringField('Section', validators=[Optional()])
    job = StringField('Job', validators=[Optional()])
    shift = SelectField('Shift', choices=[('Pagi', 'Pagi'), ('Sore', 'Sore'), ('Malam', 'Malam')], validators=[Optional()])
    submit = SubmitField('Register')


class ReportForm(FlaskForm):
    time = StringField('Time (e.g., 07:00)', validators=[DataRequired()])
    category = SelectField('Category', choices=[('Quality','Quality'),('Cost','Cost'),('Delivery','Delivery'),('Productivity','Productivity')], validators=[DataRequired()])
    title = StringField('Label / Title', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    item_name = StringField('Item name', validators=[Optional()])
    part_number = StringField('Part number', validators=[Optional()])
    customer = StringField('Customer', validators=[Optional()])
    submit = SubmitField('Save')


class SettingsForm(FlaskForm):
    name = StringField('Full name', validators=[DataRequired()])
    department = StringField('Department', validators=[Optional()])
    section = StringField('Section', validators=[Optional()])
    job = StringField('Job', validators=[Optional()])
    shift = SelectField('Shift', choices=[('Pagi', 'Pagi'), ('Sore', 'Sore'), ('Malam', 'Malam')], validators=[Optional()])
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional(), EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('Confirm New Password', validators=[Optional()])
    submit = SubmitField('Save Settings')


class AdminEditUserForm(FlaskForm):
    name = StringField('Full name', validators=[DataRequired()])
    employee_id = StringField('Employee ID', validators=[DataRequired()])
    department = StringField('Department', validators=[Optional()])
    section = StringField('Section', validators=[Optional()])
    job = StringField('Job', validators=[Optional()])
    shift = SelectField('Shift', choices=[('Pagi', 'Pagi'), ('Sore', 'Sore'), ('Malam', 'Malam')], validators=[Optional()])
    new_password = PasswordField('New Password (leave blank to keep current)', validators=[Optional()])
    is_admin = SelectField('Role', choices=[('0', 'Regular User'), ('1', 'Admin')], validators=[Optional()])
    submit = SubmitField('Update User')
