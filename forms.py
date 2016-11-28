from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, PasswordField, IntegerField, validators

class StockForm(FlaskForm):
    name = StringField("Name", [validators.input_required()])
    description = StringField("Description", [validators.optional()])
    count = IntegerField('Count', [validators.NumberRange(min=0, message="You cannot have negative stock")])

