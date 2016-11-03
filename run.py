from flask import Flask, render_template, redirect, flash
from flask_restless import APIManager
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

from app.form import MatchForm
from app.utils import remove_whitespace, flash_errors

from sqlalchemy import Column, Integer, Text, create_engine, MetaData
from trueskill import Rating, quality_1vs1, rate_1vs1

import pandas as pd
import time


def create_app():
    app = Flask(__name__, static_url_path='')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pong.db'
    Bootstrap(app)

    return app

app = create_app()
app.secret_key = 'supersecret'
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

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
metadata = MetaData(bind=engine)


@app.route('/')
def homepage():
    paragraph = '''
    This is an app to track Ping Pong games, and then calculate
    player ratings using TrueSkill. Please contact Will Eaton if you would like features added.
    '''
    return render_template("index.html", paragraph=paragraph)


@app.route('/games', methods=['GET'])
def matches():
    df = pd.read_sql('select * from game', con=engine)
    df = df.to_dict('records')
    return render_template('gamelog.html', games=df)


@app.route('/record_match', methods=['GET', 'POST'])
def record_match():
    form = MatchForm(csrf_enabled=False)
    if form.validate_on_submit():
        record = Game(player_a=form.player_a.data, player_b=form.player_b.data,
                      score_a=form.score_a.data, score_b=form.score_b.data,
                      timestamp=time.time())
        db.session.add(record)
        db.session.commit()
        return redirect('/games')
    else:
        flash_errors(form)
    return render_template('addmatch.html', form=form)


@app.route('/ratings', methods=['GET'])
def ratings():
    games = pd.read_sql('select * from game', con=engine)

    games.player_a = games.player_a.apply(remove_whitespace)
    games.player_b = games.player_b.apply(remove_whitespace)

    all_players = set(list(games.player_a.unique()) + list(games.player_b.unique()))

    ratings = {k :Rating() for k in all_players}

    for row in games.iterrows():
        if row[1]['score_a'] > row[1]['score_b']:
            ratings[row[1]['player_a']], ratings[row[1]['player_b']] = rate_1vs1(
                ratings[row[1]['player_a']], ratings[row[1]['player_b']])
        elif row[1]['score_a'] < row[1]['score_b']:
            ratings[row[1]['player_b']], ratings[row[1]['player_a']] = rate_1vs1(
                ratings[row[1]['player_b']], ratings[row[1]['player_a']])
        else:
            ratings[row[1]['player_a']], ratings[row[1]['player_b']] = rate_1vs1(
                ratings[row[1]['player_a']], ratings[row[1]['player_b']], drawn=True)

    ratingdf = pd.DataFrame()
    for k, v in ratings.iteritems():
        ratingdf.loc[k, 'Rating'] = v.mu
        ratingdf.loc[k, 'Sigma'] = v.sigma
        ratingdf.loc[k, 'TrueSkill'] = v.exposure

    ratingdf.reset_index(inplace=True)
    ratingdf = ratingdf.to_dict('records')

    return render_template('ratings.html', data=ratingdf)


if __name__ == '__main__':
    app.run(debug=True)
