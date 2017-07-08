import itertools
import logging
import time
from collections import OrderedDict
from datetime import datetime

import pandas as pd
import pytz
from flask import Flask, flash, redirect, render_template, request
from flask_admin import Admin
from flask_bootstrap import Bootstrap
from flask_cache import Cache
from flask_compress import Compress
from sqlalchemy import MetaData, create_engine, exists
from sqlalchemy.orm import sessionmaker

from app.admin import DoublesView, GameView, PlayerView, RatingsView
from app.form import DoublesMatchForm, MatchForm, PlayerForm
from app.model import DoublesGame, Game, Player, Ratings, db
from app.plots import dist_plot, win_probability_matrix
from app.ratings import (calculate_doubles_ratings, calculate_ratings,
                         calculate_team_ratings, win_probability)
from app.utils import flash_errors, rating_df_to_dict

cache = Cache(config={'CACHE_TYPE': 'simple'})
compress = Compress()


def create_app(cache):
    app = Flask(__name__, static_url_path='')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pong.db'
    cache.init_app(app)
    compress.init_app(app)
    Bootstrap(app)

    db.init_app(app)
    with app.app_context():
        db.create_all()

        admin = Admin(app, name='pongr', template_mode='bootstrap3')
        admin.add_view(GameView(Game, db.session))
        admin.add_view(DoublesView(DoublesGame, db.session))
        admin.add_view(PlayerView(Player, db.session))
        admin.add_view(RatingsView(Ratings, db.session))

    return app, cache


app, cache = create_app(cache)
app.secret_key = 'supersecret'


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
    singles = pd.read_sql(db.session.query(Game).filter(Game.deleted == 0).statement, db.session.bind)
    doubles = pd.read_sql(db.session.query(DoublesGame).filter(Game.deleted == 0).statement, db.session.bind)

    timezone = pytz.timezone('America/New_York')

    for frame in [singles, doubles]:
        frame['timestamp'] = frame['timestamp'].apply(
            datetime.fromtimestamp, tz=timezone).dt.strftime('%Y-%m-%d %H:%M:%S %Z')

    return render_template('gamelog.html', singles_games=singles.to_dict('records'),
                           doubles_games=doubles.to_dict('records'))


@app.route('/record_match', methods=['GET', 'POST'])
def record_match():
    s = '''
    select
    alias,
    printf('%s %s', first_name, last_name) as name
    from player
    '''
    choices = pd.read_sql(s, con=engine)
    choice_list = sorted([(i['alias'], i['name']) for i in choices.to_dict('records')])

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
    sql = '''
    select
    alias,
    printf('%s %s', first_name, last_name) as name
    from player
    '''
    choices = pd.read_sql(sql, con=engine)
    choice_list = sorted([(i['alias'], i['name']) for i in choices.to_dict('records')])

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

        push_new_doubles_ratings(con=engine)

        return redirect('/games')
    else:
        flash_errors(form)

    return render_template('adddoubles.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = PlayerForm(csrf_enabled=False)

    if request.method == 'POST' and form.validate_on_submit():
        if db.session.query(exists().where(Player.alias == form.alias.data)).scalar():
            flash('Alias already taken! Are you registered already?', category='warn')
        else:
            record = Player(alias=form.alias.data.lower(), first_name=form.first_name.data,
                            last_name=form.last_name.data)
            db.session.add(record)
            db.session.commit()
            return redirect('/record_match')

        return render_template('register.html')

    else:
        flash_errors(form)

    return render_template('register.html')


@cache.cached(timeout=60)
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

    s_team = '''
        select
            player1,
            player2,
            rating,
            sigma,
            trueskill
        from team_doubles_ratings
        --left join player using (alias)
        order by 3 desc
        '''

    s_rating_df = pd.read_sql(s, con=engine)
    d_rating_df = pd.read_sql(s.replace('ratings', 'doubles_ratings'), con=engine)
    t_rating_df = pd.read_sql(s_team, con=engine)


    chart = dist_plot(s_rating_df)

    singles_rating_df_4_template = s_rating_df.copy()

    s_rating_df = s_rating_df.to_dict('records')
    d_rating_df = d_rating_df.to_dict('records')
    t_rating_df = t_rating_df.to_dict('records')
    # top is for the data table as records, bottom is TrueSkill objects
    s_r_dict = rating_df_to_dict(singles_rating_df_4_template)

    rdo = OrderedDict(sorted(s_r_dict.items(), key=lambda x: x[1].mu, reverse=True))

    percent_df = pd.DataFrame()

    for pair in list(itertools.combinations_with_replacement(rdo, 2)):
        prob = win_probability(rdo[pair[0]], rdo[pair[1]])
        percent_df.loc[pair[0], pair[1]] = prob
        percent_df.loc[pair[1], pair[0]] = 1 - prob

    matrix = win_probability_matrix(percent_df)

    return render_template('ratings.html', singles_ratings=s_rating_df,
                           doubles_ratings=d_rating_df, team_df=t_rating_df,
                           dist=chart, matrix=matrix)


@app.route('/test', methods=['GET'])
def test_chart():
    import pandas as pd
    from pandas_highcharts.core import serialize
    from pandas.compat import StringIO
    dat = """ts;A;B;C
    2015-01-01 00:00:00;27451873;29956800;113
    2015-01-01 01:00:00;20259882;17906600;76
    2015-01-01 02:00:00;11592256;12311600;48
    2015-01-01 03:00:00;11795562;11750100;50
    2015-01-01 04:00:00;9396718;10203900;43
    2015-01-01 05:00:00;14902826;14341100;53"""
    df = pd.read_csv(StringIO(dat), sep=';', index_col='ts', parse_dates=['ts'])

    # Basic line plot
    chart = serialize(df, render_to='my-chart', output_type='json')

    return render_template('test_chart.html', chart=chart)



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

    team_ratingdf = calculate_team_ratings(games)
    team_ratingdf = (team_ratingdf
        .reset_index()
        .rename(columns={'index': 'team'})
        .drop('level_0', axis=1)
        )

    team_ratingdf.to_sql('team_doubles_ratings', con=con, if_exists='replace', index=False)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8008)
