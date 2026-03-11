import numpy as np
import pandas as pd
from generic.pandas_apply_parallel import *
from functools import partial
from scipy.stats import norm
from typing import *


from students.estimate_distr_from_features_subset import _qhat_full_distribution_given_qhat_sub

def q_underline_low_by_group(group:str,
                             schools_df:pd.DataFrame,
                             equilibrium_thresholds:dict, #indexed by school type
                             parameters:dict,
                             ):

    q_underline_low = {}
    
    q_tilde_1_star = equilibrium_thresholds["a"] #J1 threshold 
    for group in parameters['GROUPS']:
        dist, mean, var = _qhat_full_distribution_given_qhat_sub(group, 
                                                                qhat_sub=0, #dummy value
                                                                parameters=parameters)
        test_cost = parameters['STUDENT_TEST_COST']
        inverse_cdf = norm.ppf(1 - test_cost/parameters['STUDENT_UTILITY']["a"],
                               loc=0, scale=1)
        q_underline_low[group] = q_tilde_1_star - inverse_cdf * np.sqrt(var)
    
    return q_underline_low
        
        
def q_underline_high_by_group(group:str,
                              schools_df:pd.DataFrame,
                              equilibrium_thresholds:dict, #indexed by school type
                              parameters:dict,
                              ):
    q_tilde_1_star = equilibrium_thresholds["a"] #J1 threshold 
    
    q_underline_high = {}
    for group in parameters['GROUPS']:
        dist, mean, var = _qhat_full_distribution_given_qhat_sub(group, 
                                                                qhat_sub=0, #dummy value
                                                                parameters=parameters)
        test_cost = parameters['STUDENT_TEST_COST']
        inverse_cdf = norm.ppf(1 - test_cost/(parameters['STUDENT_UTILITY']["a"]
                                              - parameters['STUDENT_UTILITY']["b"]),
                               loc=0, scale=1)
        q_underline_high[group] = q_tilde_1_star - inverse_cdf * np.sqrt(var)
    
    return q_underline_high




function_mappers_two_schools_analytical_quantities = {
    x.__name__: x for x in [
        q_underline_low_by_group,
        q_underline_high_by_group
    ]
}