import copy
import pandas as pd

from students.settings import *
from students.helpers import *


def from_distribution(parameters):
    p = parameters
    students = []
    grouplist = []
    

    for group in range(p["NUM_GROUPS"]):
        groupletter = chr(ord("A") + group)  # ascii trick to convert group number to letter
        grouplist.append(groupletter)
        p["TRUESKILL_DIST_{}".format(groupletter)] = p.get(
            "TRUESKILL_DIST_{}".format(groupletter), p["TRUESKILL_DIST"]
        )  # get true skill distribution for that group. If not present in the parameter dictionary, default back a generic TRUESKILL_DIST
        true_skill_sampling = get_sampling_function(p["TRUESKILL_DIST_{}".format(groupletter)])
        feature_samplings = []
        for feat in range(p["NUM_FEATURES"]):
            p["FEATURE_DIST_{}{}".format(groupletter, feat)] = p.get("FEATURE_DIST_{}{}".format(groupletter, feat), p["FEATURE_DIST"])
            feature_sampling = get_sampling_function(
                p["FEATURE_DIST_{}{}".format(groupletter, feat)]
            )  # get feature distribution for that groupfeature. If not present in the parameter dictionary, default back a generic FEATURE_DIST
            feature_samplings.append(feature_sampling)
        # print(feature_samplings)
        for studnum in range(0, int(p["NUM_STUDENTS"] * p["FRACTIONS_GROUPS"][group])):
            stud = {"skill": true_skill_sampling(0), "group": groupletter}
            stud.update({"feature_{}".format(x): feature_samplings[x](stud["skill"]) for x in range(p["NUM_FEATURES"])})
            if (
                p["DO_STUDENT_BUDGETS"] and np.random.rand() > p["PROB_MEETS_BUDGET_{}".format(groupletter)]
            ):  # if doing budget case and student does not meet budget reqt, set the last feature (the test score) to nan
                stud.update({"feature_{}".format(p["NUM_FEATURES"] - 1): np.nan})
            students.append(stud)

    p["GROUPS"] = grouplist
    return pd.DataFrame(students), p


function_mappers = {x.__name__: x for x in [from_distribution]}


def create_students(func="from_distribution", parameters={}):
    students, p = function_mappers[func](parameters)
    return students, p

