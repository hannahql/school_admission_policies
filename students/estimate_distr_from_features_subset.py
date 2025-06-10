from functools import partial

import students


# Calculates distribution of test score, given other features. 
def _test_score_distribution(student_features, group,  parameters):
    features_to_use = -1
    trudisttype, truemean, truevar = parameters["TRUESKILL_DIST"]

    numerator = truemean * (truevar ** -1)
    var_invsum = truevar ** -1
    for feature in range(parameters["NUM_FEATURES"] + features_to_use):
        disttype, mean, var = parameters["FEATURE_DIST_{}{}".format(group, feature)]
        numerator += (student_features[feature] - mean) * (var ** -1)
        var_invsum += var ** -1
    qtilde = numerator / var_invsum
    tausquared = 1 / var_invsum
    
    feature = parameters["NUM_FEATURES"]-1 # select test feature
    test_disttype, test_mean, test_var = parameters["FEATURE_DIST_{}{}".format(group, feature)]
    
    test_var_given_other_features = var_invsum + test_var**(-1)
    test_mean_given_other_features = test_mean + qtilde
    
    return (test_disttype, test_mean_given_other_features, test_var_given_other_features)

# Returns test score distribution for each student
def test_score_distribution(row,  parameters):
    features_to_use = -1
    group = row["group"]
    student_features = [row["feature_{}".format(feature)] for feature in range(parameters["NUM_FEATURES"] + features_to_use)]
    
    return _test_score_distribution(student_features, group,  parameters)


#adds all test score distributions to students_df
def add_test_distributions_to_df(students_df, parameters):
    estimate_partial = partial(test_score_distribution, parameters=parameters)
    
    students_df.loc[:, "test_score_dist"] = students_df.apply(estimate_partial, axis=1)
    #return students_df
    


def _qhat_full_distribution_given_qhat_sub(#student_features, 
                                              group,  
                                              qhat_sub, 
                                              parameters,
                                              ):
    """
    Calculates distribution of qhat_full, given qhat_sub.
    """
    #group = row['group']
    trudisttype, truemean, truevar = parameters["TRUESKILL_DIST"]
    
    qhat_full_disttype = "NORMAL"
    qhat_full_mean = qhat_sub

    
    test_feature = parameters["NUM_FEATURES"]-1 # select test feature
    test_disttype, test_mean, test_var = parameters["FEATURE_DIST_{}{}".format(group, test_feature)]
    
    # Implements EC.19 from MS submission
    
    # FIRST TERM
    numerator_l = 1/test_var
    numerator_r = 1
    denominator_l = 1/truevar
    denominator_r = 1/truevar
    
    for feature in range(parameters["NUM_FEATURES"] -1): #exclude test
        disttype, mean, var = parameters["FEATURE_DIST_{}{}".format(group, feature)]
        denominator_l += 1/var
        denominator_r += 1/var
        
    denominator_l += 1/test_var 
    
    qhat_full_var = ((numerator_l/denominator_l)**2 
                     * test_var + numerator_r/denominator_r )
    
    return qhat_full_disttype, qhat_full_mean, qhat_full_var

def qhat_full_distribution_given_qhat_sub(row, 
                                          parameters,
                                          ):
    group = row['group']
    qhat_sub = row["normal_learning_aware-1_score"]
    #student_features = [row["feature_{}".format(feature)] for feature in range(parameters["NUM_FEATURES"] -1)]
    return _qhat_full_distribution_given_qhat_sub(group, qhat_sub,parameters)
    

def add_qhat_full_distribution_to_df(students_df, parameters):
    estimate_partial = partial(qhat_full_distribution_given_qhat_sub, parameters=parameters)
    students_df.loc[:, "qhat_full_dist_given_qhat_sub"] = students_df.apply(estimate_partial, axis=1)
    return students_df
