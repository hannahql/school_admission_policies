import numpy as np
from schools.admission_functions import *
from generic.pandas_apply_parallel import *
from functools import partial

def _admit_students(school_row, students_df, parameters):
    score_str = '{}{}_score'.format(school_row.estimation_function,school_row.features_to_use)
    capacity = int(np.round(school_row.capacity*parameters['NUM_STUDENTS']))
    add_function = school_row.admission_function
    return function_mappers[add_function](students_df, score_str, parameters,capacity)

def admit_students_single_school(students_df, schools_df, params):
    if params["DO_AFFIRMATIVE_ACTION"]:
        students_by_group = {group: df for group, df in students_df.groupby('group')}
        params_by_group = params.copy()
        for group in students_by_group.keys():
            params_by_group['CAPACITY'] = params_by_group['CAPACITY'] * params_by_group["AA_FRACTIONS"][group]
            students_df=students_by_group[group]
            admit_students_partial = partial(_admit_students, 
                                             students_df=students_df, 
                                             parameters=params_by_group)
            schools_df.loc[:,'admitted_students_{}'.format(group)] = schools_df.apply(admit_students_partial, axis = 1)
        schools_df['admitted_students'] = (schools_df[['admitted_students_' + group for group in students_by_group.keys()]]
                                        .agg(sum, axis=1)
                                        )
        students_df = pd.concat(students_by_group.values())
    else:
        admit_students_partial = partial(_admit_students, students_df = students_df, parameters = params)
        schools_df.loc[:,'admitted_students'] = schools_df.apply(admit_students_partial, axis = 1)
    return schools_df

def admit_students_market(students_df, schools_df, params):
    #Loop through schools, get who they admit in order. remaining schools can only consider the remaining students
    remaining_students = list(students_df.index)
    schools_df.loc[:,'admitted_students'] = np.nan

    for i in range(params['NUM_SCHOOLS']):
        ind = schools_df.index[schools_df.school_ranking == i].tolist()[0]
        school = schools_df.loc[ind] #grab school that's ranked i
        admitted_students = _admit_students(school, students_df = students_df.iloc[remaining_students], parameters = params)
        # admitted_students = admitted_students_from_remaining#(students_df.iloc[remaining_students]).iloc[admitted_students_from_remaining].index.tolist()
        remaining_students = [x for x in remaining_students if x not in admitted_students]
        schools_df.loc[schools_df.index[[ind]],'admitted_students'] =pd.Series([admitted_students], index = schools_df.index[[ind]]) #have to do this ugly trick bc trying to set a list to an element
    schools_df.loc[:,'admitted_students'] = schools_df.loc[:,'admitted_students'].apply(list)
    return schools_df
