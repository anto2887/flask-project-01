# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired

class CreateGroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired()])
    league = RadioField('League', choices=[('Premier League', 'Premier League'), ('La Liga', 'La Liga'), ('UCL', 'UEFA Champions League')], validators=[DataRequired()])
    users = SelectMultipleField('Users', coerce=int)
    submit = SubmitField('Create Group')
