from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    RadioField,
    SelectField,
)
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask import request


class LoginForm(FlaskForm):
    username = StringField("Username : ", validators=[DataRequired()])
    password = PasswordField("Password :", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    username = StringField("Username :", validators=[DataRequired()])
    email = StringField("Email :", validators=[DataRequired(), Email()])
    org = StringField("Organization :", validators=[DataRequired()])
    role = SelectField(
        "Role :", choices=[("1", "Manufacturer"), ("2", "Broker"), ("3", "Retailer")]
    )
    location = StringField("Location :", validators=[DataRequired()])
    details = StringField("Details :")
    password = PasswordField("Password :", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )

    submit = SubmitField("Register")


class ManufacturerForm(FlaskForm):
    serialnumber = StringField("Batch Number :", validators=[DataRequired()])
    cost = StringField("Cost :", validators=[DataRequired()])
    private_key = StringField("Private Key :", validators=[DataRequired()])
    quantity = StringField("Quantity :", validators=[DataRequired()])
    submit = SubmitField("Create")


class BrokerForm(FlaskForm):
    # manu_username = StringField('Owner Username :', validators=[DataRequired()])
    username = StringField("Buyer Username :", validators=[DataRequired()])
    serialnumber = StringField("Serial Number :", validators=[DataRequired()])
    private_key = StringField("Private Key :", validators=[DataRequired()])
    quantity = StringField("Quantity :", validators=[DataRequired()])
    submit = SubmitField("Transfer")


class TrackForm(FlaskForm):
    serialnumber = StringField("Serial Number:", validators=[DataRequired()])
    submit = SubmitField("Track")


class SearchForm(FlaskForm):
    search = StringField("Search :", validators=[DataRequired()])
    submit = SubmitField("Search")
    # def __init__(self, *args, **kwargs):
    #     if 'formdata' not in kwargs:
    #         kwargs['formdata'] = request.args
    #     if 'csrf_enabled' not in kwargs:
    #         kwargs['csrf_enabled'] = False
    #     super(SearchForm, self).__init__(*args, **kwargs)


class Purchase_O(FlaskForm):
    po_rx = StringField("Send PO to :", validators=[DataRequired()])
    prod_name = StringField("Product Name :", validators=[DataRequired()])
    amount = StringField("Value :", validators=[DataRequired()])
    quantity = StringField("Quantity:", validators=[DataRequired()])
    TC = StringField("Details :", validators=[DataRequired()])
    submit = SubmitField("Publish")


class Sales_O(FlaskForm):
    so_rx = StringField("Send SO to:", validators=[DataRequired()])
    org = StringField("Organisation:", validators=[DataRequired()])
    loc_ship = StringField("Shipping Address :", validators=[DataRequired()])
    quant = StringField("Quantity :", validators=[DataRequired()])
    amount = StringField("Amount :", validators=[DataRequired()])
    TC = StringField("Details :", validators=[DataRequired()])
    submit = SubmitField("Submit Sales Order")


class EndTrans(FlaskForm):
    so_id = StringField("SO ID:", validators=[DataRequired()])
    submit = SubmitField("Complete transaction")
