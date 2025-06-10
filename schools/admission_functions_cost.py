import numpy as np
from scipy.stats import norm
import pandas as pd

#import students.estimate_distr_from_features_subset
import students.test_decision_features
import itertools
#import create_students


from functools import partial
from typing import *


# Constrain search space to either the top half or the bottom half ( +/- some wiggle room)
# of the student skill distribution, depending on school capacity.
def thresholds_to_search(params, students_df):
    if params["CAPACITY"] < 0.5:
        min_skill = params['TRUESKILL_DIST'][1] - params['TRUESKILL_DIST'][2] # mean - var
        max_skill = students_df.skill.max()
    else:
        min_skill = students_df.skill.min()
        max_skill = params['TRUESKILL_DIST'][1] + params['TRUESKILL_DIST'][2] # mean + var
    thresholds_list = np.linspace(min_skill, max_skill, params["BINARY_SEARCH_NUM_THRESHOLDS"])
    return thresholds_list


def students_admitted_at_threshold(students_df, 
                                   qhat_threshold, 
                                   params,
                                   #affirmative_action=False, #if True, qhat_threshold is a dictionary
                                   ):
    students.test_decision_features.add_decision_features_to_df(students_df, qhat_threshold, params)

    applicants = students_df.query("take_test_at_threshold==True")  #students who apply
    accepted = list(applicants.query("normal_learning_aware0_score>="+str(qhat_threshold)).index)
    #num_students_accepted = len(accepted)
    return accepted

def number_admitted_at_threshold(students_df, threshold, params):
    accepted = students_admitted_at_threshold(students_df, threshold, params)
    return len(accepted)

# FOR A SINGLE SCHOOL
# Finds threshold giving number of admitted students close to capacity limit.
# Sometimes returns admitted students > capacity. In this case, threshold should have been
# next largest threshold in the list. Taken care of in `find_equilibrium_and_admit`.
def binary_search_across_thresholds(thresholds_list, students_df, capacity, params):
    
    if len(thresholds_list)==1:
        n_admitted = {}    
        threshold = thresholds_list[0]
        
        students_admitted = students_admitted_at_threshold(students_df, threshold, params)
        
        return students_admitted, threshold
    
    mid = int(len(thresholds_list)/2)
    threshold = thresholds_list[mid]
    students_admitted = students_admitted_at_threshold(students_df, threshold, params)
    n_admitted = len(students_admitted)
    if n_admitted < capacity and len(thresholds_list[:mid])>0:
        return binary_search_across_thresholds(thresholds_list[:mid], students_df, capacity, params)
    elif n_admitted > capacity and len(thresholds_list[mid+1:])>0:
        return binary_search_across_thresholds(thresholds_list[mid+1:], students_df, capacity, params)
    else:
        return students_admitted, threshold


# FOR A SINGLE SCHOOL
def find_equilibrium_and_admit(school_row, students_df, thresholds_list, params):
    capacity = school_row["capacity"] * params["NUM_STUDENTS"]
    students_admitted, threshold =  binary_search_across_thresholds(thresholds_list, students_df, capacity, params)
    if len(students_admitted) <= capacity:
        return students_admitted, threshold
    else: # when more students admitted than capacity, use next largest threshold
        new_threshold = thresholds_list[thresholds_list.tolist().index(threshold)+1]
        return students_admitted_at_threshold(students_df, new_threshold, params), new_threshold
        


# ACROSS ALL SCHOOLS
# Add admitted students to df, along with equilibrium threshold on qhat (estimated skill on full K features)
def admit_students_with_costs(students_df, schools_df, params):
    thresholds_list = thresholds_to_search(params, students_df)
    
    # admits students to each school, if there are multiple copies (not a market setting)
    admit_students_partial = partial(find_equilibrium_and_admit, students_df=students_df, 
                                     thresholds_list=thresholds_list, params=params)
    schools_df['admitted_students'], schools_df['equil_threshold'] = zip(*schools_df.apply(admit_students_partial, axis=1))
    
    schools_df['admitted_students'] = schools_df['admitted_students'].map(lambda x:list(x)) #convert tuple of admitted students to list
    return schools_df


def admit_students_with_costs_by_group(students_df, schools_df, params):
    """
    Admits students to schools, with costs varying by group.
    Called when params["SIMULATION_TYPE"] == "SINGLE_SCHOOL_COST_MODEL"
    and params["DO_AFFIRMATIVE_ACTION"] is True.
    """
    students_by_group = {group: df for group, df in students_df.groupby('group')}
    for group in students_by_group.keys():
        params_by_group = params.copy()
        params_by_group['CAPACITY'] = params_by_group['CAPACITY'] * params_by_group["AA_FRACTIONS"][group]
        thresholds_list = thresholds_to_search(params, students_by_group[group])
        students_df = students_by_group[group]
        
        admit_students_partial = partial(find_equilibrium_and_admit, 
                                         students_df=students_df, 
                                     thresholds_list=thresholds_list, 
                                     params=params_by_group)
        schools_df['admitted_students_{}'.format(group)], schools_df['equil_threshold_{}'.format(group)] = zip(*schools_df.apply(admit_students_partial, axis=1))
        
        schools_df['admitted_students_{}'.format(group)] = schools_df['admitted_students_{}'.format(group)].map(lambda x:list(x)) #convert tuple of admitted students to list
        students_by_group[group] = students_df

    schools_df['admitted_students'] = (schools_df[['admitted_students_' + group for group in students_by_group.keys()]]
                                        .agg(sum, axis=1)
                                        )
    students_df = pd.concat(students_by_group.values())
    
    return schools_df, students_df