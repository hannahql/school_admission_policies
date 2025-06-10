import students
from students.decision_functions import *
from students.decision_functions import function_mappers
#from students.decision_functions_mult_schools import *
#from students.decision_functions_mult_schools import function_mappers_two_schools


from functools import partial
from generic.pandas_apply_parallel import *

def test_decision_features(student_row, params, decision_function, qhat_threshold):
    return function_mappers[decision_function](student_row, qhat_threshold, params)
    
def add_decision_features_to_df(students_df, qhat_threshold,  parameters):
    decision_pathways = ["cost_to_test", 
                         "prob_accept_at_threshold", 
                         "exp_utility_from_school",
                         "take_test_at_threshold",
                         ]
    for feature in decision_pathways:
        decision_func = students.test_decision_features.function_mappers[feature]
        decision_partial = partial(decision_func, qhat_threshold=qhat_threshold, parameters=parameters)
        
        students_df.loc[:, feature] = students_df.apply(decision_partial, axis=1)