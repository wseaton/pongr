import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.mlab as mlab
from pandas_highcharts.core import serialize
from io import BytesIO
import seaborn as sns

def dist_plot(rating_df):
    x = np.linspace(0, 50, 500)

    data_dict = {}
    for row in rating_df.iterrows():
        label_name = (row[1]['first_name'] + ' ' + row[1]['last_name'][0] + '.')
        data_dict[label_name] = (x, mlab.normpdf(x, row[1]['rating'], row[1]['sigma']))

    final_df = pd.DataFrame()

    for k, v in data_dict.iteritems():
        final_df[k] = v[1]

    final_df['index'] = x
    final_df.set_index('index', inplace=True)

    return serialize(final_df, render_to='my-chart', title='', output_type="json")

def win_probability_matrix(matrix_df):
    '''returns a win probability matrix plot as bytecode'''
    plt.style.use('ggplot')

    f, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(matrix_df, cmap=plt.cm.viridis_r, square=True,
                cbar_kws={"shrink": .5, "label":"win pct (y)"}, ax=ax)

    plt.title('Win Probability Matrix')
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.xlabel('loser', fontsize=12)
    plt.ylabel('winner', fontsize=12)

    # We change the fontsize of minor ticks label
    plt.tick_params(axis='both', which='major', labelsize=12)


    byte = BytesIO()
    plt.savefig(byte)
    byte.seek(0)
    import base64
    figdata_png = base64.b64encode(byte.getvalue())
    return figdata_png
