import students
# from students.decision_functions import *
# from students.decision_functions import function_mappers
from students.decision_functions_mult_schools import *
from students.decision_functions_mult_schools import function_mappers_two_schools
from students.decision_functions_mult_schools import acceptance_probability


from functools import partial
from generic.pandas_apply_parallel import *



def test_decision_features_two_schools(student_row, 
                                       schools_df, 
                                       decision_function, 
                                       qhat_thresholds,
                                       parameters
                                       ):
    return function_mappers_two_schools[decision_function](student_row, schools_df, parameters, 
                                                           qhat_thresholds
                                                           )


        
def add_decision_features_to_df_mult_schools(students_df, 
                                             schools_df,
                                             qhat_thresholds, 
                                             parameters
                                             ):
    decision_pathways = [#"utility_mult_schools",
                         #"prob_accept_at_threshold_mult_schools",
                         #'expected_return_mult_schools',
                         #"acceptance_probability",
                         "exp_utility_mult_schools_test",
                         "exp_utility_mult_schools_no_test",
                         "take_test_at_thresholds_mult_schools"
                         ]
    
    for feature in decision_pathways:
        #print(feature)
        #for school_type in schools_df.school_type.unique():
        decision_func = students.test_decision_features_mult_schools.function_mappers_two_schools[feature]
        decision_partial = partial(decision_func, 
                                    schools_df=schools_df,
                                    parameters=parameters,
                                    qhat_thresholds=qhat_thresholds, 
                                )
        
        students_df.loc[:, feature] = students_df.apply(decision_partial, axis=1)
    
    # Add acceptance probabilities to the DataFrame
    acceptance_prob_partial = partial(acceptance_probability, 
                                      schools_df=schools_df,
                                      qhat_thresholds=qhat_thresholds, 
                                      parameters=parameters)
    
    acceptance_probs = students_df.apply(acceptance_prob_partial, axis=1)
    students_df["prob_accept_a"] = acceptance_probs["prob_accept_a"]
    students_df["prob_accept_b"] = acceptance_probs["prob_accept_b"]

