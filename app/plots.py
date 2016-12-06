import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.mlab as mlab
from pandas_highcharts.core import serialize

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
