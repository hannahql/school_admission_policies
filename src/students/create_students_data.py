import pandas as pd
from schools import estimation_functions_empirical_helpers as efeh
from os import path
import numpy as np


def data_column_mapper(df):
    mapp = {"GENDER_R": "Gender", "YRSQUAL": "EducationYrs", "EARNMTHALLPPP": "MonthlyIncome"}
    return df.rename(columns=mapp)


def create_students_data(parameters, folder="C:/Users/Nikhi/OneDrive/src/SAT_NRMP_project/data/"):
    df = data_column_mapper(pd.read_csv("{}df_{}.csv".format(folder, parameters["label"])))
    cols = [
        x
        for y in [[parameters["skill"], parameters["group"], parameters.get("budget_column", None)], parameters["features"]]
        for x in y
        if x is not None
    ]
    df = df[cols].dropna()
    num_features = len(parameters["features"])
    renamedict = {parameters["features"][x]: "feature_" + str(x) for x in range(num_features)}
    renamedict[parameters["group"]] = "group"
    renamedict[parameters["skill"]] = "skill"
    df = df.rename(columns=renamedict)
    groupdfs = []
    empirical_label = parameters["label"] + "_" + "".join(cols)
    parameters_students = parameters
    parameters_students.update(
        {
            "NUM_STUDENTS": parameters["NUM_STUDENTS"],
            "NUM_FEATURES": num_features,
            "empiricallabel": empirical_label,
            "NUM_GROUPS": len(parameters["group_cats"]),
        }
    )
    groups = []
    emplabelwithoutfeaturesgroup = parameters["label"] + "_" + parameters["skill"]

    df = df[df.group.isin(parameters["group_cats"])]

    for en, x in enumerate(parameters["group_cats"]):
        groupchr = chr(ord("A") + en)
        df["group"] = df.group.str.replace(x, groupchr)
        groupcount = int(parameters["NUM_STUDENTS"] * parameters["group_fractions"][en])
        dfsample = df[df.group == groupchr].sample(groupcount, replace=True)

        groupdfs.append(dfsample)
        parameters_students.update(
            {
                "FEATURE_DIST_{}{}".format(groupchr, feat): [
                    "{}_{}{}".format(emplabelwithoutfeaturesgroup, x, parameters["features"][feat])
                ]
                for feat in range(num_features)
            }
        )
        parameters_students["TRUESKILL_DIST_{}".format(groupchr)] = ["{}_{}".format(emplabelwithoutfeaturesgroup, x)]

        # storing the relevant df in proper format for the data empirical estimation of skill
        param_dist_for_filename = {
            "FEATURE_DIST_{}".format(feat): parameters_students["FEATURE_DIST_{}{}".format(groupchr, feat)] 
            for feat in range(num_features)
        }
        for features_to_use in [0, -1]:
            num_features_loc = num_features + features_to_use
            empiricalfeaturepdfname = efeh.get_empirical_feature_filename(num_features_loc, param_dist_for_filename)
            # print(empiricalfeaturepdfname)
            if not path.exists(empiricalfeaturepdfname):
                df[df.group == groupchr][[col for col in df.columns if col != "group"]].to_csv(empiricalfeaturepdfname, index=False)
        groups.append(groupchr)

    df = pd.concat(groupdfs).reset_index().drop(columns=["index"])
    if parameters["DO_STUDENT_BUDGETS"] and "budget_column" in parameters:
        df.loc[df[parameters["budget_column"]] < parameters["budget_threshold_to_apply"], "feature_{}".format(num_features - 1)] = np.nan
    elif parameters["DO_STUDENT_BUDGETS"]:
        randcol = pd.Series(np.random.rand(df.shape[0]))
        groupbudget = df.group.replace({x: parameters["PROB_MEETS_BUDGET_{}".format(x)] for x in df.group.unique()})
        df.loc[randcol > groupbudget, "feature_{}".format(num_features - 1)] = np.nan

    parameters_students["GROUPS"] = groups
    return df, parameters_students
