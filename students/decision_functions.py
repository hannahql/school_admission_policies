import numpy as np
from generic.pandas_apply_parallel import *
from functools import partial
from scipy.stats import norm


# Converts threshold on qhat (estimated skill on full K features) 
# to threshold on test score
def qhat_threshold_to_test_threshold(row, 
                                     qhat_threshold, 
                                     parameters):

    group = row['group']
    trudisttype, truemean, truevar = parameters["TRUESKILL_DIST"]
    
    feature_test= parameters["NUM_FEATURES"] -1 # test
    test_disttype, test_mean, test_var = parameters["FEATURE_DIST_{}{}".format(group, feature_test)]
    
    numerator = qhat_threshold * (truevar**-1 + test_var**-1 - truemean*(truevar**-1))
    
    for feature in range(parameters["NUM_FEATURES"] -1): #exclude test
        disttype, mean, var = parameters["FEATURE_DIST_{}{}".format(group, feature)]        
        numerator -= (row[feature] - mean) * (var ** -1)
        numerator += (var**-1) * qhat_threshold
    
        
    test_threshold = numerator * (test_var**-1) + test_mean
    return test_threshold
    
def cost_to_test(row, 
                 qhat_threshold, 
                 parameters):

    if type(parameters["STUDENT_TEST_COST"])==dict:
        group = row['group']
        return parameters["STUDENT_TEST_COST"][group]
    else:
        return parameters["STUDENT_TEST_COST"]

# Student's probability of acceptance, given a threshold on qhat (estimated skill)
def prob_accept_at_threshold(row, 
                             qhat_threshold, 
                             parameters):
    (test_score_dist, test_mean, test_var) = row['test_score_dist']
    
    test_threshold = qhat_threshold_to_test_threshold(row, qhat_threshold, parameters)
    
    # This assumes a threshold on the student's test score. This threshold must depend on 
    # student's other features
    prob_accept = 1 - norm.cdf(test_threshold, loc=test_mean, scale=np.sqrt(test_var))
    return prob_accept

#params must specify values for "STUDENT_TEST_COST" and "STUDENT_UTILITY"
def take_test_at_threshold(row, 
                           qhat_threshold, 
                           parameters):
    """
    row - student row
    """
    prob_accept = prob_accept_at_threshold(row, qhat_threshold, parameters)
    if type(parameters["STUDENT_TEST_COST"])==dict:
        group = row["group"]
        take_test = (parameters["STUDENT_TEST_COST"][group] <= parameters["STUDENT_UTILITY"]*prob_accept)
    else:
        take_test = (parameters["STUDENT_TEST_COST"] <= parameters["STUDENT_UTILITY"]*prob_accept)
    return take_test

def exp_utility_from_school(row, qhat_threshold, parameters):
   
    expected_utility = (prob_accept_at_threshold(row, qhat_threshold,  parameters) 
                        * parameters["STUDENT_UTILITY"]
                        )
    return expected_utility


# Function mappers

function_mappers = {
    x.__name__: x for x in [cost_to_test, prob_accept_at_threshold, take_test_at_threshold,
                            exp_utility_from_school,
                            ]
}
