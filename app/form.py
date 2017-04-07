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


class DoublesMatchForm(FlaskForm):
    player_a_team_a = SelectField('player_a_team_a', coerce=str)
    player_b_team_a = SelectField('player_b_team_a', coerce=str)
    player_a_team_b = SelectField('player_a_team_b', coerce=str)
    player_b_team_b = SelectField('player_b_team_b', coerce=str)
    score_team_a = IntegerField('score_team_a', validators=[DataRequired()])
    score_team_b = IntegerField('score_team_b', validators=[DataRequired()])

