import numpy as np

"""
Find out the index each element would become if this were sorted
Trick courtesy: https://stackoverflow.com/questions/5284646/rank-items-in-an-array-using-python-numpy-without-sorting-array-twice
"""


def get_rank_of_each_item(ar):
    temp = np.argsort(ar)
    ranks = np.empty_like(temp)
    ranks[temp] = np.arange(len(ar))
    return temp
