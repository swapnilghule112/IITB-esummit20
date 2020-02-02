from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField,RadioField,SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo


class LoginForm(FlaskForm):
    username = StringField('Username : ', validators=[DataRequired()])
    password = PasswordField('Password :', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username :', validators=[DataRequired()])
    email = StringField('Email :', validators=[DataRequired(), Email()])
    role = SelectField('Role :',choices=[('1','Manufacturer'), ('2','Broker'),('3','Retailer')])
    password = PasswordField('Password :', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    
    submit = SubmitField('Register')
 
class ManufacturerForm(FlaskForm):
    serialnumber = StringField('Serial Number :', validators=[DataRequired()])
    cost = StringField('Cost :', validators=[DataRequired()])
    private_key = StringField('Private Key :', validators=[DataRequired()])
    submit = SubmitField('Create')

class BrokerForm(FlaskForm):
    # manu_username = StringField('Owner Username :', validators=[DataRequired()])
    username = StringField('Buyer Username :', validators=[DataRequired()])
    serialnumber = StringField('Serial Number :', validators=[DataRequired()])
    private_key = StringField('Private Key :', validators=[DataRequired()])
    submit = SubmitField('Transfer')

class TrackForm(FlaskForm):
    serialnumber = StringField('Serial Number:', validators=[DataRequired()])
    submit = SubmitField('Track')

class SearchForm(FlaskForm):
    search = StringField('Search :' , validators=[DataRequired()])
    submit = SubmitField('Search')
    
