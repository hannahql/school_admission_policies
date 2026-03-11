from operator import itemgetter
import numpy as np
from functools import partial


def separate_distribution_column(df, colname):
    def itemgetterloc(x, ind):
        if type(x) == float:
            return np.nan
        if len(x) > ind:
            return x[ind]
        return np.nan

    # Not exactly general case if not a 2 parameter distribution with mean and variance
    df.loc[:, "{}_disttype".format(colname)] = df[colname].apply(partial(itemgetterloc, ind=0))  # get first item of
    df.loc[:, "{}_mean".format(colname)] = df[colname].apply(partial(itemgetterloc, ind=1))  # get first item of
    df.loc[:, "{}_var".format(colname)] = df[colname].apply(partial(itemgetterloc, ind=2))  # get first item of
