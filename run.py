from flask import Flask, render_template
from flask.ext.restless import APIManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap

from sqlalchemy import Column, Integer, Text, create_engine, MetaData
import pandas as pd
import time

def create_app():
    app = Flask(__name__, static_url_path='')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pong.db'
    Bootstrap(app)

    return app

app = create_app()
db = SQLAlchemy(app)

class Game(db.Model):
    id = Column(Integer, primary_key=True)
    player_a = Column(Text, unique=False)
    player_b = Column(Text, unique=False)
    score_a = Column(Integer, unique=False)
    score_b = Column(Integer, unique=False)
    timestamp = Column(Integer, unique=False)

db.create_all()

api_manager = APIManager(app, flask_sqlalchemy_db=db)
api_manager.create_api(Game, methods=['GET', 'POST', 'DELETE', 'PUT'])

class MatchForm(FlaskForm):
    player_a = StringField('player_a', validators=[DataRequired()])
    player_b = StringField('player_b', validators=[DataRequired()])
    score_a = IntegerField('score_a', validators=[DataRequired()])
    score_b = IntegerField('score_b', validators=[DataRequired()])

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
metadata = MetaData(bind=engine)

@app.route('/', methods=['GET', 'POST'])
def matches():
    df = pd.read_sql('select * from game', con=engine)
    df = df.to_dict('records')
    return render_template('index.html', games=df)

@app.route('/record_match', methods=['GET', 'POST'])
def record_match():
    form = MatchForm(csrf_enabled=False)
    if form.validate_on_submit():
        record = Game(player_a=form.player_a.data, player_b=form.player_b.data,
                      score_a=form.score_a.data, score_b=form.score_b.data,
                      timestamp=time.time())
        db.session.add(record)
        db.session.commit()
        return 'success! your match was uploaded.'

    return render_template('addmatch.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
