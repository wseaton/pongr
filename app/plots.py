import matplotlib.pyplot as plt
import numpy as np
import matplotlib.mlab as mlab
import mpld3

def dist_plot(rating_df):
    x = np.linspace(0, 50, 500)

    f = plt.figure(figsize=(16,8))
    a=f.add_subplot(111)

    for row in rating_df.iterrows():
        norm = mlab.normpdf(x, row[1]['rating'], row[1]['sigma'])
        plt.plot(x, norm, linewidth=2, label=row[1]['first_name'])

    legend = plt.legend(frameon = 1, loc='upper left', title='')
    frame = legend.get_frame()
    frame.set_edgecolor('grey')
    plt.style.use('fivethirtyeight')
    plt.title('Rating Distributions', fontsize=18)

    return  mpld3.fig_to_html(f)
