import schools
from schools.estimation_functions import *
from schools.estimation_functions import function_mappers

from functools import partial
from generic.pandas_apply_parallel import *

def estimate_skill(student_row, parameters, features_to_use, estimation_function):
    return function_mappers[estimation_function](student_row, features_to_use, parameters)

#adds all student estimation scores to the student df
def add_all_skillestimates_to_df(students_df, schools_df, parameters,
                                 add_full_and_sub_skill_estimate=False):
    
    if add_full_and_sub_skill_estimate:
        # Add both full (0) and subset (-1) features for each estimation function
        unique_estfunctions = set(schools_df.estimation_function)
        unique_estfunctions_feature_pairs = set()
        for est_func in unique_estfunctions:
            unique_estfunctions_feature_pairs.add((est_func, 0))  # Full features
            unique_estfunctions_feature_pairs.add((est_func, -1)) # Subset features 
    else:
        # Only add the features_to_use specified in the schools_df
        unique_estfunctions_feature_pairs=set(list(zip(schools_df.estimation_function,schools_df.features_to_use)))
    for est_function_str,features_to_use in unique_estfunctions_feature_pairs:
        est_func = schools.estimate_skill.function_mappers[est_function_str]
        estimate_partial = partial(est_func, parameters = parameters, features_to_use =features_to_use)

        score_str = '{}{}_score'.format(est_function_str,features_to_use)

        students_df.loc[:,score_str] = students_df.apply(estimate_partial, axis = 1)
