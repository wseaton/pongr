import pandas as pd
from trueskill import Rating, quality_1vs1, rate_1vs1
from .utils import remove_whitespace

def calculate_ratings(game_df, rating_object=Rating()):
    '''
    calculates player ratings and outputs a summary dataframe of results
    '''

    game_df.player_a = game_df.player_a.apply(remove_whitespace)
    game_df.player_b = game_df.player_b.apply(remove_whitespace)

    all_players = set(list(game_df.player_a.unique()) + list(game_df.player_b.unique()))

    ratings = {k :rating_object for k in all_players}

    for row in game_df.iterrows():
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
        ratingdf.loc[k, 'rating'] = v.mu
        ratingdf.loc[k, 'sigma'] = v.sigma
        ratingdf.loc[k, 'tau'] = v.tau
        ratingdf.loc[k, 'pi'] = v.pi
        ratingdf.loc[k, 'trueskill'] = v.exposure

    ratingdf.reset_index(inplace=True)

    return ratingdf
