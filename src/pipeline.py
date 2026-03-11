import copy
#from generic.latexify import *
from generic.pandas_apply_parallel import *
import multiprocessing


import settings
import students.settings
from students.create_students import create_students#, split_students_by_group

import schools
import schools.settings
import schools.settings_cost_model
import schools.settings_cost_model_mult_schools
from schools.create_schools import create_schools
import schools.estimate_skill
import schools.admit_students
import schools.admission_functions_cost_mult_schools

from students.create_students_data import create_students_data
import students.estimate_distr_from_features_subset
import students.test_decision_features
import schools.admission_functions_cost 
import students.add_analytical_quantities_mult_schools

from evaluations import metrics


"""
Main code that runs simulations for a given set of parameters.

Values for SIMULATION_TYPE:
"SINGLE_SCHOOL" -- One school only. 
"MARKET" -- Multiple schools. Randomizes order of school rankings. 
For each school type t, creates int(NUM_SCHOOLS * FRACTION_OF_SCHOOL_TYPES[t]) copies of this school.
"MARKET_FIX_SCHOOL_ATTRIBUTES" -- Multiple schools. Allows user to specify ranking of schools. Pass in school names and rankings.
"""
def pipeline(custom_parameters): 
    params = copy.deepcopy(settings.default_parameters)
    params.update(students.settings.default_parameters)
    params.update(schools.settings.default_parameters)
    
    params.update(schools.settings_cost_model.default_parameters)
    if params["SIMULATION_TYPE"] == "TWO_SCHOOL_COST_MODEL":
        params.update(schools.settings_cost_model_mult_schools.default_parameters)
    params.update(custom_parameters)

    if params.get("loading_from_data", False):
        students_df, params = create_students_data(parameters=params)
    else:
        students_df, params = create_students(parameters=params)
    schools_df, params = create_schools(parameters=params)

    schools.estimate_skill.add_all_skillestimates_to_df(students_df, schools_df, params)

    if params["SIMULATION_TYPE"] == "SINGLE_SCHOOL":
        schools_df = schools.admit_students.admit_students_single_school(students_df, schools_df, params)
    elif params["SIMULATION_TYPE"] in ["MARKET", "MARKET_FIX_SCHOOL_ATTRIBUTES"]:
        schools_df = schools.admit_students.admit_students_market(students_df, schools_df, params)
    elif params["SIMULATION_TYPE"] == "SINGLE_SCHOOL_COST_MODEL":
        if params["DO_AFFIRMATIVE_ACTION"]:
            students.estimate_distr_from_features_subset.add_test_distributions_to_df(students_df, params)
            schools_df, students_df = schools.admission_functions_cost.admit_students_with_costs_by_group(students_df, 
                                                                                schools_df, 
                                                                                params)
            
        else:
            students.estimate_distr_from_features_subset.add_test_distributions_to_df(students_df, params)
            
            schools_df = schools.admission_functions_cost.admit_students_with_costs(students_df, 
                                                                                    schools_df, 
                                                                                    params)
    elif params["SIMULATION_TYPE"] == "TWO_SCHOOL_COST_MODEL":
        schools.estimate_skill.add_all_skillestimates_to_df(students_df, 
                                                            schools_df, 
                                                            params,
                                                            add_full_and_sub_skill_estimate=True)
        students.estimate_distr_from_features_subset.add_test_distributions_to_df(students_df, params)
        students.estimate_distr_from_features_subset.add_qhat_full_distribution_to_df(students_df, params)
        
        schools_df = schools.admission_functions_cost_mult_schools.admit_students_with_costs_mult_schools(students_df, 
                                                                                                              schools_df, 
                                                                                                              params)
        students.add_analytical_quantities_mult_schools.add_q_underline_values_to_df(students_df, 
                                                                                     schools_df, 
                                                                                     params)
    metrics.calculate_all_metrics(students_df, schools_df, params)

    return students_df, schools_df, params


