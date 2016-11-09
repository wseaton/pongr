from flask import Flask, render_template, redirect, flash
from flask_restless import APIManager
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

from app.form import MatchForm
from app.utils import remove_whitespace, flash_errors
from app.ratings import calculate_ratings

from sqlalchemy import Column, Integer, Text, create_engine, MetaData, Float
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


class Player(db.Model):
    player_id =  Column(Integer, primary_key=True)
    first_name = Column(Text, unique=False)
    last_name = Column(Text, unique=False)
    alias = Column(Text, unique=True)


class Ratings(db.Model):
    alias = Column(Text, primary_key=True)
    rating = Column(Float, unique=False)
    sigma = Column(Float, unique=False)
    tau = Column(Float, unique=False)
    pi = Column(Float, unique=False)
    trueskill = Column(Float, unique=False)


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

        push_new_ratings(con=engine)

        return redirect('/games')
    else:
        flash_errors(form)
    return render_template('addmatch.html', form=form)


@app.route('/ratings', methods=['GET'])
def ratings():
    ratingdf = pd.read_sql('select * from ratings', con=engine)
    ratingdf = ratingdf.to_dict('records')

    return render_template('ratings.html', data=ratingdf)


@app.route('/delete/<game_id>', methods=['POST'])
def delete_game(game_id):
    Game.query.filter_by(id=game_id).delete()
    db.session.commit()

    push_new_ratings(con=engine)

    return redirect('/games')


def push_new_ratings(con=None):
    '''
    recalculates player ratings and pushes them to the database
    '''
    games = pd.read_sql('select * from game', con=con)

    ratingdf = calculate_ratings(games)
    ratingdf = (ratingdf.reset_index().rename(columns={'index':'alias'})
                .drop('level_0', axis=1))

    ratingdf.to_sql('ratings', con=con, if_exists='replace', index=False)


if __name__ == '__main__':
    app.run(debug=True)
