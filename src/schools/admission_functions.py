import numpy as np

# Function that turns any overall admission function into a per-group-function
def admission_pergroup_generic(admission_func, students_df, score_col, parameters, capacity):
    # loop through each group, grab their capacity (by fraction) for each group, and then do the admissions within that group
    admitted = []
    if (parameters["NUM_GROUPS"] == 2) and ("FRAC_GROUPS_ADMIT_A" not in parameters.keys()):
        parameters["FRAC_GROUPS_ADMIT_A"] = 1 - parameters["FRAC_GROUPS_ADMIT_B"]
    for group in students_df.group.unique():
        students_group = students_df.query('group == "{}"'.format(group))
        capacity_group = int(
            np.floor(parameters["FRAC_GROUPS_ADMIT_{}".format(group)] * capacity)
        )  # This is naive way -- if capacities aren't integer, will actually admit less than supposed to, but up to NUM_GROUPS students
        admitted_group = admission_func(
            students_group, score_col, parameters, capacity_group
        )  # these index into the group-specific df, not overall df

        admitted.extend(admitted_group)
    return list(admitted)


def estimated_skill_ranking(students_df, score_col, parameters, capacity):
    scores = -students_df[score_col].values
    order = np.argsort(scores)
    admitted = order[0:capacity]
    return list(students_df.iloc[admitted].index)


def estimated_skill_ranking_pergroup(students_df, score_col, parameters, capacity):
    return admission_pergroup_generic(estimated_skill_ranking, students_df, score_col, parameters, capacity)


function_mappers = {x.__name__: x for x in [estimated_skill_ranking, estimated_skill_ranking_pergroup]}
