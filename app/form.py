from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, Length

class MatchForm(FlaskForm):
    player_a = StringField('player_a', validators=[DataRequired(), Length(max=20)])
    player_b = StringField('player_b', validators=[DataRequired(), Length(max=20)])
    score_a = IntegerField('score_a', validators=[DataRequired(), Length(max=2)])
    score_b = IntegerField('score_b', validators=[DataRequired(), Length(max=2)])
