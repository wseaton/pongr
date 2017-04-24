import matplotlib.mlab as mlab
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.offline as offl


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

    trace_dict = dict()

    for n, col in enumerate(final_df.columns):
        trace_dict[n] = go.Scatter(
            x=final_df.index,
            y=final_df[col],
            name=col
        )

    data = trace_dict.values()

    # Edit the layout
    layout = dict(title='Individual Gaussian Skill Distribution',
                  xaxis=dict(title='Mu'),
                  yaxis=dict(title='Value'),
                  )

    return offl.plot(dict(data=data, layout=layout), output_type='div')


def win_probability_matrix(matrix_df):
    'returns the win probability matrix plot as a plotly heatmap'

    trace = go.Heatmap(
        z=matrix_df.transpose().values.tolist(),
        x=matrix_df.columns[::-1],
        y=matrix_df.columns[::-1],
        colorscale='Viridis'
    )

    data = [trace]

    layout = go.Layout(
        title='Win Probability Matrix',
        xaxis=dict(title='Loser', ticks=''),
        yaxis=dict(title='Winner', ticks='')
    )

    return offl.plot(dict(data=data, layout=layout), output_type='div')
