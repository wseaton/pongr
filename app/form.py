from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length

class MatchForm(FlaskForm):
    player_a = SelectField('player_a', coerce=str)
    player_b = SelectField('player_b', coerce=str)
    score_a = IntegerField('score_a', validators=[DataRequired()])
    score_b = IntegerField('score_b', validators=[DataRequired()])


class PlayerForm(FlaskForm):
    alias = StringField('alias', validators=[DataRequired()])
    first_name = StringField('first_name', validators=[DataRequired()])
    last_name = StringField('first_name', validators=[DataRequired()])
