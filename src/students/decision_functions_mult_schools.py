import numpy as np
import pandas as pd
from generic.pandas_apply_parallel import *
from functools import partial
from scipy.stats import norm



"""
decision_functions_mult_schools.py

Contains functions related to student test-taking behavior in a two school context.
Given two schools' policies and thresholds, it calculates expected utility for taking tests and not taking tests.
Students decide whether to take the test by comparing these two utilities. 

This code is called by admission_functions_cost_mult_schools.py

Key Functions:
- exp_utility_mult_schools_test: Calculates expected utility for taking tests
- exp_utility_mult_schools_no_test: Calculates expected utility without taking tests  
- take_test_at_thresholds_mult_schools: Determines if student should take test
- add_decision_features_to_df_mult_schools: Adds decision-related features to student dataframe
"""



def _prob_accept_at_threshold_given_qhat_dist(qhat_mean: float,
                                             qhat_var: float,
                                             threshold: float) -> float:
    """
    Helper function, called for dif combos of school policies and student test decisions.
    Does not distinguish between whether qhat distribution is based on all features or K-1 features.
    
    Input:
    - qhat_mean: mean of qhat distribution
    - qhat_var: variance of qhat distribution
    - threshold: threshold on qhat
    """
    prob_accept = 1 - norm.cdf(threshold, loc=qhat_mean, scale=np.sqrt(qhat_var))
    return prob_accept
    



def acceptance_probability(student_row: pd.Series, 
                           schools_df: pd.DataFrame, 
                           qhat_thresholds: dict, 
                           parameters: dict) -> pd.Series:
    """
    Calculate the probability of acceptance to school A and school B for a given student,
    taking into account each school's test policy.

    Parameters:
    - student_row: A pandas Series representing a student's data.
    - schools_df: DataFrame containing school data.
    - qhat_thresholds: Dictionary with thresholds for each school.
    - parameters: Dictionary with additional parameters, including student utility and features to use.

    Returns:
    - A pandas Series with the acceptance probabilities for school A and school B.
    """
    # Extract necessary values from the student_row
    disttype, qhat_full_mean, qhat_full_var = student_row['qhat_full_dist_given_qhat_sub']
    qhat_sub = student_row['normal_learning_aware-1_score']
    
    # Determine school policies
    school_policies = {"a": parameters['FEATURES_TO_USE_a'], 
                       "b": parameters['FEATURES_TO_USE_b']}
    
    # Calculate acceptance probability for school A
    if school_policies['a'] == 0:  # School A requires a test
        prob_accept_a = _prob_accept_at_threshold_given_qhat_dist(
            qhat_full_mean, qhat_full_var, qhat_thresholds['a']
        )
    elif school_policies['a'] == -1:  # School A does not require a test
        prob_accept_a = float(qhat_sub > qhat_thresholds['a'])
    else:
        raise ValueError("Invalid policy for school A")
    
    # Calculate acceptance probability for school B
    if school_policies['b'] == 0:  # School B requires a test
        prob_accept_b = _prob_accept_at_threshold_given_qhat_dist(
            qhat_full_mean, qhat_full_var, qhat_thresholds['b']
        )
    elif school_policies['b'] == -1:  # School B does not require a test
        prob_accept_b = float(qhat_sub > qhat_thresholds['b'])
    else:
        raise ValueError("Invalid policy for school B")
    
    return pd.Series({"prob_accept_a": prob_accept_a, "prob_accept_b": prob_accept_b})




def exp_utility_mult_schools_test(row:pd.Series, 
                                  schools_df: pd.DataFrame,
                                  qhat_thresholds:dict, 
                                  parameters:dict
                                  ) -> float:
    """
    Returns expected utility from taking the test and subtracts cost of test.
    
    Computes expected utility for preferred school and expected utility
    for less preferred school, conditional on not being admitted to preferred school.
    """
    school_policies = {"a": parameters['FEATURES_TO_USE_a'], 
                       "b": parameters['FEATURES_TO_USE_b']}
    
    disttype, qhat_full_mean, qhat_full_var = row['qhat_full_dist_given_qhat_sub']
    qhat_sub = row['normal_learning_aware-1_score']
    
    # Determine school preferences based on rank
    school_ranks = schools_df.set_index("school_type")["school_rank"].to_dict()
    preferred_school = min(school_ranks, key=school_ranks.get)
    less_preferred_school = "b" if preferred_school == "a" else "a"
    
    if school_policies[preferred_school] == 0: # school a requires test, student will apply to school a
        prob_accept_a = _prob_accept_at_threshold_given_qhat_dist(qhat_full_mean,
                                                                qhat_full_var,
                                                                qhat_thresholds[preferred_school])
        utility_a = prob_accept_a * parameters["STUDENT_UTILITY"][preferred_school]
        
        if school_policies[less_preferred_school] == 0: # school b requires test, student will apply to school b
            # probability of rejection at school a and acceptance at school b
            prob_accept_b = _prob_accept_at_threshold_given_qhat_dist(qhat_full_mean,
                                                                qhat_full_var,
                                                                qhat_thresholds[less_preferred_school])
            
            # student only accepts school b if they are rejected at school a
            # Can subtract because both schools use same evaluation function
            prob_reject_a_and_accept_b = prob_accept_b - prob_accept_a
            utility_b = prob_reject_a_and_accept_b * parameters["STUDENT_UTILITY"][less_preferred_school]

        elif school_policies[less_preferred_school] == -1:
            accept_b = qhat_sub > qhat_thresholds[less_preferred_school]
            # student only accepts school b if they are rejected at school a
            utility_b = (1-prob_accept_a) * accept_b * parameters["STUDENT_UTILITY"][less_preferred_school]
        
    elif school_policies[preferred_school] == -1:
        accept_a = qhat_sub > qhat_thresholds[preferred_school] #deterministic, based on qhat_sub
        utility_a = accept_a * parameters["STUDENT_UTILITY"][preferred_school]
        if school_policies[less_preferred_school] == 0:
            prob_accept_b = _prob_accept_at_threshold_given_qhat_dist(qhat_full_mean,
                                                                qhat_full_var,
                                                                qhat_thresholds[less_preferred_school])
            # student only accepts school b if they are rejected at school a
            utility_b = (1-accept_a)* (prob_accept_b * parameters["STUDENT_UTILITY"][less_preferred_school])
        elif school_policies[less_preferred_school] == -1:
            accept_b = qhat_sub > qhat_thresholds[less_preferred_school]
            utility_b = (1-accept_a)* accept_b * parameters["STUDENT_UTILITY"][less_preferred_school]
    else:
        raise ValueError("Invalid school policies")
    total_utility = utility_a + utility_b - parameters["STUDENT_TEST_COST"]
    return total_utility
            
    
    
def exp_utility_mult_schools_no_test(row:pd.Series, 
                                    schools_df: pd.DataFrame,
                                    qhat_thresholds:dict, 
                                    parameters:dict,
                                    ):
    """
    Calculate expected utilities from not taking the test.
    Computes expected utility for preferred school and expected utility
    for less preferred school, conditional on not being admitted to preferred school.

    """
    
    qhat_sub = row['normal_learning_aware-1_score']
    
    # Determine school preferences based on rank
    school_ranks = schools_df.set_index("school_type")["school_rank"].to_dict()
    preferred_school = min(school_ranks, key=school_ranks.get)
    less_preferred_school = "b" if preferred_school == "a" else "a"
    
    school_policies = {"a": parameters['FEATURES_TO_USE_a'], 
                       "b": parameters['FEATURES_TO_USE_b']}
    
    if school_policies[preferred_school] == 0: # school a requires test, student will not apply to school a
        prob_accept_a = 0
        utility_a = prob_accept_a * parameters["STUDENT_UTILITY"][preferred_school]
        
        if school_policies[less_preferred_school] == 0: # school b requires test, student will not apply to school b
            prob_reject_a_and_accept_b = 0
            utility_b = prob_reject_a_and_accept_b * parameters["STUDENT_UTILITY"][less_preferred_school]

        elif school_policies[less_preferred_school] == -1: # school b does not require test, student will apply to school b
            accept_b = qhat_sub > qhat_thresholds["b"]
            utility_b = accept_b * parameters["STUDENT_UTILITY"][less_preferred_school]
        
    elif school_policies[preferred_school] == -1: # school a does not require test
        accept_a = qhat_sub > qhat_thresholds["a"] #deterministic, based on qhat_sub
        utility_a = accept_a * parameters["STUDENT_UTILITY"][preferred_school]
        if school_policies[less_preferred_school] == 0: # school b requires test, student will not apply to school b
            prob_accept_b = 0
            utility_b = (1-accept_a)* (prob_accept_b * parameters["STUDENT_UTILITY"][less_preferred_school])
        elif school_policies[less_preferred_school] == -1: # school b does not require test, student will apply to school b
            accept_b = qhat_sub > qhat_thresholds["b"] #deterministic, based on qhat_sub
            utility_b = (1-accept_a)* accept_b * parameters["STUDENT_UTILITY"][less_preferred_school]
    else:
        raise ValueError("Invalid school policies")

    total_utility = utility_a + utility_b
    return total_utility




def take_test_at_thresholds_mult_schools(row, 
                                        schools_df: pd.DataFrame,
                                        qhat_thresholds, 
                                        # qhat_threshold_test, 
                                        # qhat_threshold_no_test,
                                        #q_test_threshold,
                                        parameters,
                                        ):
    """
    Given two schools admission thresholds qhat_thresholds and the 
    schools' policies (use all features or drop test), returns True if student decides to take the test.
    
    Implements separately for each combination of school policies.
    
    Inputs:
    - qhat_thresholds: dict, indexed by school, values are thresholds on qhat. 
        Agnostic of whether qhat is based on all features or K-1 features.
    """
    utility_test = exp_utility_mult_schools_test(row, schools_df, qhat_thresholds, parameters)
    utility_no_test = exp_utility_mult_schools_no_test(row, schools_df, qhat_thresholds, parameters)
    
    return utility_test >= utility_no_test







function_mappers_two_schools = {
    x.__name__: x for x in [#utility_mult_schools,
                         #prob_accept_at_threshold_mult_schools,
                         acceptance_probability,
                         exp_utility_mult_schools_test,
                         exp_utility_mult_schools_no_test, 
                         take_test_at_thresholds_mult_schools,
                         ]
}
