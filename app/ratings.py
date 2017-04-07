import pandas as pd
import numpy as np
from trueskill import Rating, rate_1vs1, rate
from trueskill import TrueSkill
from itertools import combinations
from .utils import remove_whitespace


def calculate_ratings(game_df, rating_object=Rating(), return_type='dataframe'):
    """
    calculates player ratings and outputs a summary dict or dataframe of results
    :param rating_object: TrueSkill object
    :param return_type: 'dict' or 'dataframe'
    :type game_df: pd.DataFrame
    """

    for col in game_df.columns:
        if 'player' in col:
            game_df[col] = game_df[col].apply(remove_whitespace)

    all_players = set(list(game_df.player_a.unique()) + list(game_df.player_b.unique()))
    ratings = {k :rating_object for k in all_players}

    for row in game_df.iterrows():
        
        player_a = ratings[row[1]['player_a']]
        player_b = ratings[row[1]['player_b']]
        
        if row[1]['score_a'] > row[1]['score_b']:
            player_a, player_b = rate_1vs1(player_a, player_b)
        elif row[1]['score_a'] < row[1]['score_b']:
            player_b, player_a = rate_1vs1(player_b, player_a)
        else:
            player_a, player_b = rate_1vs1(player_a, player_b, drawn=True)

        ratings[row[1]['player_a']] = player_a
        ratings[row[1]['player_b']] = player_b

    if return_type == 'dict':
        return ratings

    elif return_type == 'dataframe':

        rating_df = pd.DataFrame()

        for k, v in ratings.iteritems():
            rating_df.loc[k, 'rating'] = v.mu
            rating_df.loc[k, 'sigma'] = v.sigma
            rating_df.loc[k, 'tau'] = v.tau
            rating_df.loc[k, 'pi'] = v.pi
            rating_df.loc[k, 'trueskill'] = v.exposure

        rating_df.reset_index(inplace=True)
        return rating_df


def calculate_doubles_ratings(game_df, rating_object=Rating(), return_type='dataframe'):
    
    for col in game_df.columns:
        if 'player' in col:
            game_df[col] = game_df[col].apply(remove_whitespace)

    all_players = set(list(game_df.player_a_team_a.unique()) + list(game_df.player_b_team_a.unique())
                    + list(game_df.player_a_team_b.unique()) + list(game_df.player_b_team_b.unique()))

    ratings = {k:rating_object for k in all_players}

    for row in game_df.iterrows():

        player_a_team_a = ratings[row[1]['player_a_team_a']]
        player_b_team_a = ratings[row[1]['player_b_team_a']]
        player_a_team_b = ratings[row[1]['player_a_team_b']]
        player_b_team_b = ratings[row[1]['player_b_team_b']]

        t_a = player_a_team_a, player_b_team_a
        t_b = player_a_team_b, player_b_team_b

        if row[1]['score_team_a'] > row[1]['score_team_b']:
            t_a, t_b = rate([t_a, t_b], ranks=[0, 1])
        elif row[1]['score_team_a'] < row[1]['score_team_b']:
            t_a, t_b = rate([t_a, t_b], ranks=[1, 0])
        else:
            t_a, t_b = rate([t_a, t_b], ranks=[0, 0])

        player_a_team_a, player_b_team_a = t_a
        player_a_team_b, player_b_team_b = t_b

        ratings[row[1]['player_a_team_a']] = player_a_team_a
        ratings[row[1]['player_b_team_a']] = player_b_team_a
        ratings[row[1]['player_a_team_b']] = player_a_team_b
        ratings[row[1]['player_b_team_b']] = player_b_team_b

    if return_type == 'dict':
        return ratings

    elif return_type == 'dataframe':

        rating_df = pd.DataFrame()

        for k, v in ratings.iteritems():
            rating_df.loc[k, 'rating'] = v.mu
            rating_df.loc[k, 'sigma'] = v.sigma
            rating_df.loc[k, 'tau'] = v.tau
            rating_df.loc[k, 'pi'] = v.pi
            rating_df.loc[k, 'trueskill'] = v.exposure

        rating_df.reset_index(inplace=True)
        return rating_df


def calculate_team_ratings(game_df):
    for col in game_df.columns:
        if 'player' in col:
            game_df[col] = game_df[col].apply(remove_whitespace)

    all_players = set(list(game_df.player_a_team_a.unique()) + list(game_df.player_b_team_a.unique())
                      + list(game_df.player_a_team_b.unique()) + list(game_df.player_b_team_b.unique()))

    teams = combinations(all_players, 2)

    ratings = {k: Rating() for k in teams}

    # todo: finish this



def win_probability(rating_a, rating_b):
    delta_mu = rating_a.mu - rating_b.mu
    rs3 = np.sqrt(rating_a.sigma**2 + rating_b.sigma**2)
    return TrueSkill(backend='scipy').cdf(delta_mu/rs3)
