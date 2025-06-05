import numpy as np
from scipy.stats import norm
import pandas as pd
#import itertools

import students.estimate_distr_from_features_subset
import students.test_decision_features_mult_schools


#from students.decision_functions_mult_schools import take_test_at_thresholds_mult_schools
from students.test_decision_features_mult_schools import add_decision_features_to_df_mult_schools
#from functools import partial
from typing import *

"""
admission_functions_cost_mult_schools.py

Contains functions related to the admission process for multiple schools,
considering costs and thresholds. 
School policies are defined by (qhat_threshold_s1, qhat_threshold_s2).
Each pair induces a different student test-taking behavior, 
as students decide whether to take the test 
based on their expected utility from taking and not taking the test 
(exp_utility_mult_schools_test and exp_utility_mult_schools_no_test).

This code searches through (qhat_threshold_s1, qhat_threshold_s2) pairs to find a pair 
that maximizes the number of admitted students while satisfying school capacities.

Functions:
- thresholds_to_search_mult_schools: Generates threshold pairs for grid search.
- students_admitted_at_thresholds: Determines which students are admitted based on thresholds.
- number_admitted_at_thresholds: Counts the number of students admitted per school.
- grid_search_across_threshold_pairs: Performs a grid search to evaluate threshold pairs.
- find_equilibrium_thresholds: Finds the optimal threshold pair for admissions.
- admit_students_with_costs_mult_schools: Main function to admit students and update dataframes.

"""




def thresholds_to_search_mult_schools(params: dict, 
                                      students_df: pd.DataFrame) -> List[dict]:
    """
    Generates a list of threshold pairs to search through for two schools (a and b).
    Determines appropriate min/max search parameters for each school.
    This function is called when min/max thresholds are not provided in parameters.
        
    Returns:
        List of dictionaries, where each dictionary contains threshold pairs {"a": thresh_a, "b": thresh_b"}
    """
    # search thresholds for school a
    if params["CAPACITY_a"] < 0.5: 
        min_skill_a = params['TRUESKILL_DIST'][1] - params['TRUESKILL_DIST'][2] # mean - var
        max_skill_a = students_df.skill.max()
    else:
        min_skill_a = students_df.skill.min()
        max_skill_a = params['TRUESKILL_DIST'][1] + params['TRUESKILL_DIST'][2] # mean + var
        
    if params["CAPACITY_a"] + params["CAPACITY_b"] < 0.5: # search thresholds for school b
        min_skill_b = params['TRUESKILL_DIST'][1] - params['TRUESKILL_DIST'][2] # mean - var
        max_skill_b = students_df.skill.max()
    else:
        min_skill_b = students_df.skill.min()
        max_skill_b = params['TRUESKILL_DIST'][1] + params['TRUESKILL_DIST'][2] # mean + var

    # Generate evenly spaced threshold values between min and max for each school
    thresholds_list_a = np.linspace(min_skill_a, max_skill_a, params["GRID_SEARCH_NUM_THRESHOLDS"])
    thresholds_list_b = np.linspace(min_skill_b, max_skill_b, params["GRID_SEARCH_NUM_THRESHOLDS"])
    
    # Create list of threshold pairs as dictionaries
    # Each dict maps school type ('a' or 'b') to its threshold value
    threshold_pairs = [{"a": thresh_a, "b": thresh_b} 
                      for thresh_a in thresholds_list_a 
                      for thresh_b in thresholds_list_b]
    return threshold_pairs


def students_admitted_at_thresholds(students_df: pd.DataFrame, 
                                    schools_df: pd.DataFrame,
                                    qhat_thresholds: dict, 
                                    parameters: dict,
                                    ) -> pd.Series:
    """
    Given school thresholds and policies, 
    1) calls function for students to decide whether to take the test and 
    2) loops through schools (in order of school rank), 
    admits students to schools based on their estimated skill.
    
    * ASSUMES NO AFFIRMATIVE ACTION
    """
    students_df = students_df.copy()
    add_decision_features_to_df_mult_schools(students_df=students_df, 
                                             schools_df=schools_df,
                                             qhat_thresholds=qhat_thresholds, 
                                             parameters=parameters
                                            )
    remaining_students = list(students_df.index)
    
    sorted_schools_df = schools_df.sort_values(by="school_rank")
    series_admitted = {}
    for index, school in sorted_schools_df.iterrows(): 
        school_type = school['school_type'] # a or b
        threshold = qhat_thresholds[school_type]
        if school['features_to_use'] == 0:
            applicants = (students_df.iloc[remaining_students]
                          .query("take_test_at_thresholds_mult_schools==True")
                          )
            admitted = list(applicants.query("normal_learning_aware0_score>="+str(threshold)).index)
        else:
            admitted = list(students_df.iloc[remaining_students]
                            .query("`normal_learning_aware-1_score`>="+str(threshold)).index)
        series_admitted[school_type] = admitted
        remaining_students = [x for x in remaining_students if x not in admitted]
    return series_admitted


def number_admitted_at_thresholds(students_df: pd.DataFrame, 
                                  schools_df: pd.DataFrame, 
                                  qhat_thresholds: dict, 
                                  parameters: dict
                                  ) -> dict:
    num_admitted = {}
    admitted_students = students_admitted_at_thresholds(students_df, schools_df, qhat_thresholds, parameters)
    num_admitted = {school_type:len(admitted_students[school_type]) 
                    for school_type in admitted_students.keys()}
    return num_admitted


def grid_search_across_threshold_pairs(threshold_pairs_array: List[dict], 
                                       students_df: pd.DataFrame, 
                                       #capacities,
                                       schools_df: pd.DataFrame,
                                       parameters: dict
                                       ) -> Tuple[dict, dict]:
    """
    Given a grid of threshold pairs, 
    returns a dictionary of number of admitted students for each threshold pair.
    
    Threshold pair is a dictionary with keys "a" and "b".
    """
    admitted_students_by_threshold_pair = {}
    num_admitted_by_threshold_pair = {}
    for threshold_pair in threshold_pairs_array:
        pair = (threshold_pair["a"], threshold_pair["b"])
        admitted_students = students_admitted_at_thresholds(students_df, 
                                                            schools_df, 
                                                            threshold_pair, 
                                                            parameters)
        admitted_students_by_threshold_pair[pair] = admitted_students
        num_admitted_by_threshold_pair[pair] = {school:len(admitted_students[school]) 
                                                          for school in admitted_students.keys()}
    return admitted_students_by_threshold_pair, num_admitted_by_threshold_pair


def find_equilibrium_thresholds(students_df: pd.DataFrame, 
                               schools_df: pd.DataFrame, 
                               qhat_thresholds_list: List[dict], 
                               parameters: dict
                               ) -> Tuple[dict, dict]:
    """
    Given school capacities, finds the threshold pair that maximizes 
    the number of admitted students while satisfying capacity constraints.
    """
    schools = schools_df.index
    threshold_pairs_tuples = [(threshold_pair["a"], threshold_pair["b"]) for threshold_pair in qhat_thresholds_list]
    
    capacities = {schools_df.loc[school,'school_type']:schools_df.loc[school,'capacity']*parameters['NUM_STUDENTS'] 
                  for school in schools
                  }
    
    admitted_students, num_admitted = grid_search_across_threshold_pairs(qhat_thresholds_list, 
                                                                        students_df, 
                                                                        schools_df, 
                                                                        parameters)
    
    
    feasible_pairs = [pair for pair in threshold_pairs_tuples  if 
                      all(num_admitted[pair][school] <= capacities[school] 
                      for school in capacities.keys())]
    
    # find the pair that maximizes the number of admitted students
    max_admitted_total = max(sum(num_admitted[pair].values()) for pair in feasible_pairs)
    max_pair_idx = feasible_pairs[np.argmax(
        [sum(num_admitted[pair].values()) for pair in feasible_pairs]
    )]
    max_admitted_per_school = num_admitted[max_pair_idx]
    
    return max_pair_idx, admitted_students[max_pair_idx]
    ## FOR DEBUGGING
    #return max_admitted_total, max_admitted_per_school, feasible_pairs, max_pair_idx, num_admitted 


def admit_students_with_costs_mult_schools(students_df: pd.DataFrame, 
                                          schools_df: pd.DataFrame, 
                                          parameters: dict
                                          ) -> pd.DataFrame:
    """
    Searches through threshold pairs to find the equilibrium thresholds 
    that maximize the number of admitted students.
    
    Adds admission decisions to students_df and schools_df.
    """
    # Check if min/max thresholds are provided in parameters
    if all(key in parameters for key in ["MIN_THRESHOLD_a", "MIN_THRESHOLD_b", 
                                       "MAX_THRESHOLD_a", "MAX_THRESHOLD_b"]):
        # Create threshold list using provided min/max values
        thresholds_a = np.linspace(parameters["MIN_THRESHOLD_a"], 
                                 parameters["MAX_THRESHOLD_a"],
                                 parameters["GRID_SEARCH_NUM_THRESHOLDS"])
        thresholds_b = np.linspace(parameters["MIN_THRESHOLD_b"],
                                 parameters["MAX_THRESHOLD_b"], 
                                 parameters["GRID_SEARCH_NUM_THRESHOLDS"])
        
        # Create list of threshold pairs as dictionaries
        qhat_thresholds_list = [{"a": a, "b": b} 
                               for a in thresholds_a 
                               for b in thresholds_b]
    else:
        # Use default threshold search function if min/max not provided
        qhat_thresholds_list = thresholds_to_search_mult_schools(params=parameters, students_df=students_df)

    
    max_pair_idx, admitted_students = find_equilibrium_thresholds(students_df, 
                                                                   schools_df, 
                                                                   qhat_thresholds_list, 
                                                                   parameters)
    # Add admission decisions to students_df based on equilibrium thresholds
    for school in schools_df.index:
        school_type = schools_df.loc[school,'school_type']

        # Update students_df with test decisions at equilibrium threshold 
        students.test_decision_features_mult_schools.add_decision_features_to_df_mult_schools(students_df=students_df, 
                                                                                            schools_df=schools_df, 
                                                                                            qhat_thresholds={"a": max_pair_idx[0], "b": max_pair_idx[1]}, 
                                                                                            parameters=parameters)
        # Get list of admitted students for this school
        admitted = admitted_students[school_type]
        
        # Create admission decision column for this school
        admission_col = f"admitted_at_{school_type}"
        students_df[admission_col] = False
        students_df.loc[admitted, admission_col] = True
        
    # add admission decisions to schools_df
    schools_df['admitted_students'] = schools_df['school_type'].map(admitted_students)
    schools_df['equil_threshold'] = max_pair_idx
    schools_df['num_admitted'] = schools_df.school_type.map(lambda x:len(admitted_students[x]))
    

    return schools_df

