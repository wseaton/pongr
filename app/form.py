from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

class MatchForm(FlaskForm):
    player_a = StringField('player_a', validators=[DataRequired()])
    player_b = StringField('player_b', validators=[DataRequired()])
    score_a = IntegerField('score_a', validators=[DataRequired()])
    score_b = IntegerField('score_b', validators=[DataRequired()])
