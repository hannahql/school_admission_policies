import numpy as np
import re
from collections import defaultdict

NEGATIVE_CONSTANT = None

def average_admitted_skill(students_df, admitted_students, parameters):
    return {"avgadmittedskill": admitted_students.skill.mean()}


def average_admitted_skill_pergroup(students_df, admitted_students, parameters):
    skills = {}
    for x in admitted_students.group.unique():
        df = admitted_students[admitted_students.group == x]
        skills["avgadmittedskill_{}".format(x)] = df.skill.mean() if not df.empty else NEGATIVE_CONSTANT
    return skills

def average_admitted_test_score(students_df, admitted_students, parameters):
    r = re.compile("feature_*")
    features = list(filter(r.match, students_df.columns))
    features.sort()
    feature_test = features[-1]  # Find last feature, this is test score
    return {'avgadmittedtestscore': admitted_students[feature_test].mean()}

def average_admitted_test_score_pergroup(students_df, admitted_students, parameters):
    test_scores = {}
    
    r = re.compile("feature_*")
    features = list(filter(r.match, students_df.columns))
    features.sort()
    feature_test = features[-1]  # Find last feature, this is test score
    for x in admitted_students.group.unique():
        df = admitted_students[admitted_students.group == x]
        test_scores["avgadmittedtestscore_{}".format(x)] = df[feature_test].mean() if not df.empty else NEGATIVE_CONSTANT
    return test_scores


def average_admitted_test_score_takers_only(students_df, admitted_students, parameters):
    """
    Calculates average test score among admitted students who took the test.
    Only used for COST_MODEL simulations where test-taking is optional.
    
    Args:
        students_df: DataFrame containing all students
        admitted_students: DataFrame containing only admitted students
        parameters: Dictionary of simulation parameters
    
    Returns:
        Dictionary with average test scores for test-takers, overall and by group
    """
    # Get test score column name (last feature)
    r = re.compile("feature_*")
    features = list(filter(r.match, students_df.columns))
    features.sort()
    feature_test = features[-1]  # Find last feature, this is test score
    
    # Filter for admitted students who took the test
    test_takers = admitted_students[admitted_students["take_test_at_thresholds_mult_schools"] == True]
    
    scores = {}
    
    # Calculate overall average
    scores["avgadmittedtestscore_testtakers"] = (test_takers[feature_test].mean() 
                                                if not test_takers.empty 
                                                else NEGATIVE_CONSTANT)
    
    # Calculate by group
    for group in admitted_students.group.unique():
        group_takers = test_takers[test_takers.group == group]
        scores[f"avgadmittedtestscore_testtakers_{group}"] = (group_takers[feature_test].mean()
                                                             if not group_takers.empty
                                                             else NEGATIVE_CONSTANT)
    
    return scores


# fraction each group admitted
def fraction_each_group(students_df, admitted_students, parameters):
    fractions = admitted_students.group.value_counts() / admitted_students.shape[0]
    fracgroups = {}

    for x in admitted_students.group.unique():
        fracgroups["frac_{}".format(x)] = fractions[x]
    return fracgroups

def prob_apply_given_skill(students_df, admitted_students, parameters, roundmult=20):
    vals_A = defaultdict(dict)
    vals_B= defaultdict(dict)
    valsskill_A= defaultdict(dict)
    valsskill_B = defaultdict(dict)

    # label admitted students
    admitted_students_index = admitted_students.index
    students_df["admitted"] = False
    students_df.loc[admitted_students_index, "admitted"] = True
    
    # bucket students into skill bins
    students_df.loc[:, "skillcut"] = (students_df.skill.rank(pct=True) * roundmult).round(1) / roundmult

    roundmultskill = int(np.ceil(roundmult / (students_df.skill.max() - students_df.skill.min()) * 2))
    students_df.loc[:, "skillround"] = (students_df.skill * roundmultskill).round(1) / roundmultskill

    concats = []
    dfsum = students_df.groupby(["group", "skillcut"])["admitted"].mean().reset_index()
    for skill in students_df.skillcut.unique():
        quera = dfsum.query('skillcut==@skill and group=="A"')
        querb = dfsum.query('skillcut==@skill and group=="B"')
        if quera.shape[0] < 1 or querb.shape[0] < 1:
            # print(school, skill)
            continue
        groupaprob = quera.iloc[0]["admitted"].astype(float)
        groupbprob = querb.iloc[0]["admitted"].astype(float)

        vals_A[skill] = groupaprob 
        vals_B[skill] = groupbprob

    dfsum = students_df.groupby(["group", "skillround"])["admitted"].mean().reset_index()
    for skill in students_df.skillround.unique():
        quera = dfsum.query('skillround==@skill and group=="A"')
        querb = dfsum.query('skillround==@skill and group=="B"')
        if quera.shape[0] < 1 or querb.shape[0] < 1:
            # print(school, skill)
            continue
        groupaprob = quera.iloc[0]["admitted"].astype(float)
        groupbprob = querb.iloc[0]["admitted"].astype(float)

        valsskill_A[skill] = groupaprob 
        valsskill_B[skill] = groupbprob
    return {"prob_apply_skill_A": vals_A, "prob_apply_skill_B":vals_B,
            "prob_apply_rawskill_A": valsskill_A, "prob_apply_rawskill_B":valsskill_B}
    

def individual_fairness(students_df, admitted_students, parameters, roundmult=20):
    vals = {}
    valsskill = {}

    admitted_students_index = admitted_students.index
    students_df["admitted"] = False
    students_df.loc[admitted_students_index, "admitted"] = True
    students_df.loc[:, "skillcut"] = (students_df.skill.rank(pct=True) * roundmult).round(1) / roundmult

    roundmultskill = int(np.ceil(roundmult / (students_df.skill.max() - students_df.skill.min()) * 2))
    students_df.loc[:, "skillround"] = (students_df.skill * roundmultskill).round(1) / roundmultskill

    concats = []
    dfsum = students_df.groupby(["group", "skillcut"])["admitted"].mean().reset_index()
    for skill in students_df.skillcut.unique():
        quera = dfsum.query('skillcut==@skill and group=="A"')
        querb = dfsum.query('skillcut==@skill and group=="B"')
        if quera.shape[0] < 1 or querb.shape[0] < 1:
            # print(school, skill)
            continue
        groupaprob = quera.iloc[0]["admitted"].astype(float)
        groupbprob = querb.iloc[0]["admitted"].astype(float)

        vals[skill] = groupaprob - groupbprob

    dfsum = students_df.groupby(["group", "skillround"])["admitted"].mean().reset_index()
    for skill in students_df.skillround.unique():
        quera = dfsum.query('skillround==@skill and group=="A"')
        querb = dfsum.query('skillround==@skill and group=="B"')
        if quera.shape[0] < 1 or querb.shape[0] < 1:
            # print(school, skill)
            continue
        groupaprob = quera.iloc[0]["admitted"].astype(float)
        groupbprob = querb.iloc[0]["admitted"].astype(float)

        valsskill[skill] = groupaprob - groupbprob
    return {"IF": vals, "IF_rawskill": valsskill}

def prob_apply_given_test_score(students_df, admitted_students, parameters, roundmult=20):
    vals_A = defaultdict(dict)
    vals_B= defaultdict(dict)
    #valstest = defaultdict(dict)
    valstest_A= defaultdict(dict)
    valstest_B = defaultdict(dict)
    
    r = re.compile("feature_*")
    features = list(filter(r.match, students_df.columns))
    features.sort()
    feature_test = features[-1]  # Find last feature, this is test score

    # label admitted students
    admitted_students_index = admitted_students.index
    students_df["admitted"] = False
    students_df.loc[admitted_students_index, "admitted"] = True
    
    # bucket students into test score bins
    students_df.loc[:, "testcut"] = (students_df[feature_test].rank(pct=True) * roundmult).round(1) / roundmult

    roundmulttest = int(np.ceil(roundmult / (students_df[feature_test].max() - students_df[feature_test].min()) * 2))
    students_df.loc[:, "testround"] = (students_df[feature_test] * roundmulttest).round(1) / roundmulttest

    concats = []
    dfsum = students_df.groupby(["group", "testcut"])["admitted"].mean().reset_index()
    for test in students_df.testcut.unique():
        quera = dfsum.query('testcut==@test and group=="A"')
        querb = dfsum.query('testcut==@test and group=="B"')
        if quera.shape[0] < 1 or querb.shape[0] < 1:
            # print(school, skill)
            continue
        groupaprob = quera.iloc[0]["admitted"].astype(float)
        groupbprob = querb.iloc[0]["admitted"].astype(float)

        vals_A[test] = groupaprob 
        vals_B[test] = groupbprob

    dfsum = students_df.groupby(["group", "testround"])["admitted"].mean().reset_index()
    for test in students_df.testround.unique():
        quera = dfsum.query('testround==@test and group=="A"')
        querb = dfsum.query('testround==@test and group=="B"')
        if quera.shape[0] < 1 or querb.shape[0] < 1:
            # print(school, skill)
            continue
        groupaprob = quera.iloc[0]["admitted"].astype(float)
        groupbprob = querb.iloc[0]["admitted"].astype(float)

        valstest_A[test] = groupaprob 
        valstest_B[test] = groupbprob
    return {"prob_apply_given_test_A": vals_A, "prob_apply_given_test_B":vals_B,
            "prob_apply_given_rawtest_A": valstest_A, "prob_apply_given_rawtest_B":valstest_B}


all_metric_funcs = [average_admitted_skill, average_admitted_skill_pergroup, fraction_each_group, 
                    individual_fairness,
                    average_admitted_test_score, average_admitted_test_score_pergroup,
                    prob_apply_given_test_score,
                    prob_apply_given_skill,
                    ]

metric_funcs_two_school_cost_model = [average_admitted_test_score_takers_only,]


def calculate_all_metrics(students_df, schools_df, parameters):
    mets = []
    unique_mets = set()
    
    #print(parameters["SIMULATION_TYPE"])
    if parameters["SIMULATION_TYPE"] == "TWO_SCHOOL_COST_MODEL":
        # Add cost model specific metrics when running TWO_SCHOOL_COST_MODEL simulation
        all_metric_funcs.extend(metric_funcs_two_school_cost_model)
    for ind, school in schools_df.iterrows():
        admitted_students = students_df.loc[school.admitted_students]
        cur_mets = {}
        for metric_func in all_metric_funcs:
            #print(metric_func)
            cur_mets.update(metric_func(students_df, admitted_students, parameters))
        mets.append(cur_mets)
        unique_mets.update(cur_mets.keys())
    #return schools_df, unique_mets, mets
    for key in unique_mets:
        schools_df.loc[:, key] = [met.get(key, 0) for met in mets]
    return schools_df
