import numpy as np
import scipy.stats
from scipy.stats import truncnorm
from functools import partial


def normal(skill, loc, scale):
    return skill + np.random.normal(loc=loc, scale=scale)


def truncated_normal(skill, loc, scale, a, b):
    val = normal(skill, loc, scale)
    return max(min(val, b), a)


def get_sampling_function(dist_parameters):
    if dist_parameters[0] == "NORMAL":
        return partial(normal, loc=dist_parameters[1], scale=dist_parameters[2] ** 0.5)
    elif dist_parameters[0] == "TRUNCATED_NORMAL":
        return partial(
            truncated_normal,
            a=dist_parameters[3],
            b=dist_parameters[4],
            loc=dist_parameters[1],
            scale=dist_parameters[2] ** 0.5,
        )
