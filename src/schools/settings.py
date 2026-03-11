default_parameters = {
    "SKILL_ESTIMATION_FUNCTION": "normal_learning_aware",
    "ADMISSION_FUNCTION": "estimated_skill_ranking",
    "FEATURES_TO_USE": 0,  # 0 indicates use all features; so school type 0 uses all features
    "SCHOOL_QUALITY": "random",  # how to order schools in students' heterogeneous preferences
    "NUM_SCHOOL_TYPES": 2,
    "FRACTIONS_SCHOOL_TYPES": [0.5, 0.5],
    "NUM_SCHOOLS": 2,
    "FEATURES_TO_USE_0": 0,  # 0 indicates use all features; so school type 0 uses all features
    "FEATURES_TO_USE_1": -1,  # School 1 uses all features except final feature
    "CAPACITY": 0.2,  # default school capacity in fraction of total number of students
    "DO_STUDENT_BUDGETS": False,
    "DO_AFFIRMATIVE_ACTION":False,
}
