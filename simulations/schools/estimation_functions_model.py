import numpy as np
import numpy.random as random
import json
import schools.estimation_functions_model_helpers as efmh

# iii. uses a regression model of some kind
group_to_model = {}


def reset_globals():
    group_to_model = {}


def _generic_model_learning(student_features, group, features_to_use, parameters):
    global group_to_model

    parameters_group = {"TRUESKILL_DIST": parameters["TRUESKILL_DIST_{}".format(group)]}
    parameters_group.update(
        {"FEATURE_DIST_{}".format(feat): parameters["FEATURE_DIST_{}{}".format(group, feat)] for feat in range(len(student_features))}
    )
    grouphash = json.dumps(parameters_group, sort_keys=True)  # creates hash for the group parameters
    # map the student groups to the df of student samples using for empirical qtilde
    # if first student in that group, loading the right one, Otherwise load from the map
    if grouphash not in group_to_model.keys():
        print(grouphash)
        group_to_model[grouphash] = efmh.load_features_model(len(student_features), parameters_group)
    model = group_to_model[grouphash]
    # print(student_features)
    prediction = model.predict([[xx for yy in [[1], student_features] for xx in yy]])[0]

    return prediction + random.uniform(-1e-6, 1e-6)


def genericdist_model_aware(row, features_to_use, parameters):
    group = row["group"]
    # print("num features at genericdistmodel", parameters["NUM_FEATURES"])
    student_features = [row["feature_{}".format(feature)] for feature in range(parameters["NUM_FEATURES"] + features_to_use)]
    if any(np.isnan(student_features)):
        return np.nan

    return _generic_model_learning(student_features, group, features_to_use, parameters)
