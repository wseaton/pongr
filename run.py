from flask import Flask, render_template, redirect, flash, request
from flask_restless import APIManager
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

from app.form import MatchForm, PlayerForm, DoublesMatchForm
from app.utils import flash_errors, rating_df_to_dict
from app.ratings import calculate_ratings, calculate_doubles_ratings, win_probability
from app.plots import dist_plot, win_probability_matrix

from sqlalchemy import Column, Integer, Text, create_engine, MetaData, Float, Boolean

import pandas as pd
import time
import itertools
import logging
from collections import OrderedDict
from datetime import datetime
import pytz

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
    deleted = Column(Boolean, unique=False)


class DoublesGame(db.Model):
    id = Column(Integer, primary_key=True)
    player_a_team_a = Column(Text, unique=False)
    player_b_team_a = Column(Text, unique=False)
    player_a_team_b = Column(Text, unique=False)
    player_b_team_b = Column(Text, unique=False)
    score_team_a = Column(Integer, unique=False)
    score_team_b = Column(Integer, unique=False)
    timestamp = Column(Integer, unique=False)
    deleted = Column(Boolean, unique=False)


class Player(db.Model):
    player_id = Column(Integer, primary_key=True)
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


@app.before_first_request
def setup_logging():
    if not app.debug:
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)


@app.route('/')
def homepage():
    paragraph = '''
    This is an app to track Ping Pong games, and then calculate
    player ratings using TrueSkill.
    '''
    return render_template("index.html", paragraph=paragraph)


@app.route('/games', methods=['GET'])
def matches():
    singles = pd.read_sql('select * from game where deleted = 0', con=engine)
    doubles = pd.read_sql('select * from doubles_game where deleted = 0', con=engine)

    tz = pytz.timezone('America/New_York')

    for frame in [singles, doubles]:

        frame['timestamp'] = frame['timestamp'].apply(datetime.utcfromtimestamp)
        frame['timestamp'] = frame['timestamp'].apply(datetime.replace, tzinfo=tz)
        frame['timestamp'] = frame['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S %Z')

    singles = singles.to_dict('records')
    doubles = doubles.to_dict('records')

    return render_template('gamelog.html', singles_games=singles, doubles_games=doubles)


@app.route('/record_match', methods=['GET', 'POST'])
def record_match():
    s = '''
    select
    alias,
    printf('%s %s', first_name, last_name) as name
    from player
    '''
    choices = pd.read_sql(s, con=engine)
    choice_list = [(i['alias'], i['name']) for i in choices.to_dict('records')]

    form = MatchForm(csrf_enabled=False)
    form.player_a.choices = choice_list
    form.player_b.choices = choice_list

    if request.method == 'POST' and form.validate_on_submit():
        record = Game(player_a=form.player_a.data, player_b=form.player_b.data,
                      score_a=form.score_a.data, score_b=form.score_b.data,
                      deleted=0, timestamp=time.time())
        db.session.add(record)
        db.session.commit()

        push_new_ratings(con=engine)

        return redirect('/games')

    else:
        flash_errors(form)

    return render_template('addmatch.html', form=form)


@app.route('/record_doubles', methods=['GET', 'POST'])
def record_doubles():
    s = '''
    select
    alias,
    printf('%s %s', first_name, last_name) as name
    from player
    '''
    choices = pd.read_sql(s, con=engine)
    choice_list = [(i['alias'], i['name']) for i in choices.to_dict('records')]

    form = DoublesMatchForm(csrf_enabled=False)
    form.player_a_team_a.choices = choice_list
    form.player_b_team_a.choices = choice_list
    form.player_a_team_b.choices = choice_list
    form.player_b_team_b.choices = choice_list

    if request.method == 'POST' and form.validate_on_submit():
        record = DoublesGame(
            player_a_team_a=form.player_a_team_a.data,
            player_b_team_a=form.player_b_team_a.data,
            player_a_team_b=form.player_a_team_b.data,
            player_b_team_b=form.player_b_team_b.data,
            score_team_a=form.score_team_a.data,
            score_team_b=form.score_team_b.data,
            deleted=0, timestamp=time.time()
        )

        db.session.add(record)
        db.session.commit()

        push_new_doubles_ratings(con=engine) # todo: update this to push doubles

        return redirect('/games')
    else:
        flash_errors(form)

    return render_template('adddoubles.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = PlayerForm(csrf_enabled=False)

    if request.method == 'POST' and form.validate_on_submit():
        record = Player(alias=form.alias.data, first_name=form.first_name.data,
                      last_name=form.last_name.data)
        db.session.add(record)
        db.session.commit()

        return redirect('/record_match')

    else:
        flash_errors(form)

    return render_template('register.html')


@app.route('/ratings', methods=['GET'])
def ratings():
    s = '''
    select
        first_name,
        last_name,
        alias,
        rating,
        sigma,
        trueskill
    from ratings
    left join player using (alias)
    order by 3 desc
    '''

    s_rating_df = pd.read_sql(s, con=engine)
    d_rating_df = pd.read_sql(s.replace('ratings', 'doubles_ratings'), con=engine)

    chart = dist_plot(s_rating_df)

    singles_rating_df_4_template = s_rating_df.copy()

    s_rating_df = s_rating_df.to_dict('records')
    d_rating_df = d_rating_df.to_dict('records')
    # top is for the data table as records, bottom is TrueSkill objects
    s_r_dict = rating_df_to_dict(singles_rating_df_4_template)

    rdo = OrderedDict(sorted(s_r_dict.items(), key=lambda x: x[1].mu, reverse=True))

    percent_df = pd.DataFrame()

    for pair in list(itertools.combinations_with_replacement(rdo, 2)):
        prob = win_probability(rdo[pair[0]], rdo[pair[1]])
        percent_df.loc[pair[0], pair[1]] = prob
        percent_df.loc[pair[1], pair[0]] = 1 - prob

    matrix = win_probability_matrix(percent_df)

    return render_template('ratings.html', singles_ratings=s_rating_df, doubles_ratings=d_rating_df,
                           dist=chart, matrix=matrix.decode('utf8'))


@app.route('/delete/<game_id>', methods=['POST'])
def delete_game(game_id):
    game = Game.query.filter_by(id=game_id).first()
    game.deleted = 1

    db.session.commit()
    push_new_ratings(con=engine)

    return redirect('/games')


@app.route('/recalculate', methods=['POST'])
def recalculate():
    push_new_ratings(con=engine)

    return redirect('/ratings')


def push_new_ratings(con=None):
    """
    recalculates player ratings and pushes them to the database
    """
    games = pd.read_sql('select * from game where deleted = 0', con=con)

    ratingdf = calculate_ratings(games)
    ratingdf = (ratingdf.reset_index().rename(columns={'index':'alias'})
                .drop('level_0', axis=1))

    ratingdf.to_sql('ratings', con=con, if_exists='replace', index=False)



def push_new_doubles_ratings(con=None):
    """
    recalculates doubles ratings and pushes them to the database
    """
    games = pd.read_sql('select * from doubles_game where deleted = 0', con=con)

    ratingdf = calculate_doubles_ratings(games)
    ratingdf = (ratingdf.reset_index().rename(columns={'index':'alias'})
                .drop('level_0', axis=1))

    ratingdf.to_sql('doubles_ratings', con=con, if_exists='replace', index=False)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8008)
