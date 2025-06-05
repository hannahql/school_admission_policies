import numpy as np
import schools.estimation_functions_empirical as efe
import schools.estimation_functions_model as efm


def _normal_learning(student_features, group, features_to_use, parameters):
    trudisttype, truemean, truevar = parameters["TRUESKILL_DIST"]

    numerator = truemean * (truevar ** -1)
    var_invsum = truevar ** -1
    for feature in range(parameters["NUM_FEATURES"] + features_to_use):
        disttype, mean, var = parameters["FEATURE_DIST_{}{}".format(group, feature)]
        numerator += (student_features[feature] - mean) * (var ** -1)
        var_invsum += var ** -1
    qtilde = numerator / var_invsum
    tausquared = 1 / var_invsum
    return qtilde


def normal_learning_aware(row, features_to_use, parameters):
    group = row["group"]
    student_features = [row["feature_{}".format(feature)] for feature in range(parameters["NUM_FEATURES"] + features_to_use)]

    return _normal_learning(student_features, group, features_to_use, parameters)


def normal_learning_unaware(row, features_to_use, parameters):
    trudisttype, truemean, truevar = parameters["TRUESKILL_DIST"]
    groupweightsum = 0  # to normalize, since I don't calculate demoninator of group weight

    qtilde = 0
    student_features = [row["feature_{}".format(feature)] for feature in range(parameters["NUM_FEATURES"] + features_to_use)]

    for en, group in enumerate(parameters["GROUPS"]):
        var_invsum = truevar ** -1
        qtildegroup = _normal_learning(student_features, group, features_to_use, parameters)
        exparg = 0
        stdproduct = 1
        for feature in range(parameters["NUM_FEATURES"] + features_to_use):
            _, mean, var = parameters["FEATURE_DIST_{}{}".format(group, feature)]
            var_invsum += var ** -1
            stdproduct *= var ** (0.5)
            exparg += ((truemean + mean - student_features[feature]) ** 2) * (var ** -1) * (truevar ** -1)

            for othfeature in range(feature + 1, parameters["NUM_FEATURES"] + features_to_use):
                _, meanoth, varoth = parameters["FEATURE_DIST_{}{}".format(group, othfeature)]
                exparg += (
                    (((meanoth - student_features[othfeature]) - (mean - student_features[feature])) ** 2) * (var ** -1) * (varoth ** -1)
                )
        exparg /= 2 * var_invsum

        groupweight = parameters["FRACTIONS_GROUPS"][en] * np.exp(-exparg) / stdproduct / (var_invsum ** (0.5))

        qtilde += qtildegroup * groupweight
        groupweightsum += groupweight
    return qtilde / groupweightsum


function_mappers = {
    x.__name__: x for x in [normal_learning_aware, normal_learning_unaware, efe.genericdist_empirical_aware, efm.genericdist_model_aware]
}
