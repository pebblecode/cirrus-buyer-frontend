from flask_wtf import Form
from wtforms import DecimalField, BooleanField
from wtforms.validators import DataRequired, Email, NumberRange
from dmutils.forms import StripWhitespaceStringField


class OrderForm(Form):
    """Order Form"""

    email_address = StripWhitespaceStringField(
        '1. Email address', id="input_email_address",
        validators=[
            DataRequired(message="You must provide an email address"),
            Email(message="You must provide a valid email address")
            ]
        )
    po_number = StripWhitespaceStringField(
        '2. PO Number', id='input_po_number',
        validators=[
            DataRequired(message="You must provide a PO Number")
            ]
        )
    amount = DecimalField(
        '3. Total Amount', id='input_amount',
        validators=[
            NumberRange(min=0, message="Total Amount needs to be positive")
            ]
        )
    have_read_buyers_guide = BooleanField(
        ''
        )
