import copy
import pandas as pd
import numpy as np

from schools.settings import *
from schools.helpers import *


def get_school_quality(parameters, school):
    if parameters["SCHOOL_QUALITY"] == "random":
        return np.random.normal()
    
def get_school_rank_cost_model(parameters, school):
    """
    Returns school rank based on student utility values.
    Higher utility = higher rank (1 being highest).
    
    Args:
        parameters: Dictionary containing simulation parameters including STUDENT_UTILITY
        school: Dictionary or Series containing school information including school_type
        
    Returns:
        int: School rank based on utility value (1 = highest utility)
    """
    # Get school type (a, b, etc)
    school_type = school["school_type"]
    
    # Get all utility values sorted in descending order
    sorted_utilities = sorted(parameters["STUDENT_UTILITY"].items(), 
                            key=lambda x: x[1], 
                            reverse=True)
    
    # Find rank of this school's utility (add 1 since rank is 0-based)
    rank = [s[0] for s in sorted_utilities].index(school_type) + 1
    
    return rank

def create_schools(parameters):
    p = parameters
    
    if p["SIMULATION_TYPE"] == "MARKET_FIX_SCHOOL_ATTRIBUTES": #allows user to pass in dictionaries mapping each school to desired attributes and rankings
        return create_schools_market_fix_attributes(p)
     
    schools = []
    
    for school_type in range(p["NUM_SCHOOL_TYPES"]):
        
        schoolletter = chr(ord("a") + school_type)  # ascii trick to convert school_type number to letter
        if p["SIMULATION_TYPE"] == "SINGLE_SCHOOL" or p["SIMULATION_TYPE"] == "SINGLE_SCHOOL_COST_MODEL":  # only create 1 school per type to compare outcomes in each realization
            number_schools_this_type = 1
            
        else:
            number_schools_this_type = int(p["NUM_SCHOOLS"] * p["FRACTIONS_SCHOOL_TYPES"][school_type])
            
        p["SKILL_ESTIMATION_FUNCTION_{}".format(schoolletter)] = p.get(
            "SKILL_ESTIMATION_FUNCTION_{}".format(schoolletter), p["SKILL_ESTIMATION_FUNCTION"]
        )

        p["CAPACITY_{}".format(schoolletter)] = p.get("CAPACITY_{}".format(schoolletter), p["CAPACITY"])
        p["ADMISSION_FUNCTION_{}".format(schoolletter)] = p.get("ADMISSION_FUNCTION_{}".format(schoolletter), p["ADMISSION_FUNCTION"])
        p["FEATURES_TO_USE_{}".format(schoolletter)] = p.get("FEATURES_TO_USE_{}".format(schoolletter), p["FEATURES_TO_USE"])
        
        for schoolnum in range(0, number_schools_this_type):
            school = {
                "school_type": schoolletter,
                "estimation_function": p["SKILL_ESTIMATION_FUNCTION_{}".format(schoolletter)],
                "capacity": p["CAPACITY_{}".format(schoolletter)],
                "admission_function": p["ADMISSION_FUNCTION_{}".format(schoolletter)],
                "features_to_use": p["FEATURES_TO_USE_{}".format(schoolletter)],
            }

            if p["SIMULATION_TYPE"] == "MARKET":
                school["school_quality"] = get_school_quality(p, school) # randomizes ordering of schools
            
        # Add rank for TWO_SCHOOL_COST_MODEL
        if p["SIMULATION_TYPE"] == "TWO_SCHOOL_COST_MODEL":
            school["school_rank"] = get_school_rank_cost_model(p, school)
       
        schools.append(school)

    schools = pd.DataFrame(schools)
    if p["SIMULATION_TYPE"] == "MARKET":
        rankings = get_rank_of_each_item((-schools.school_quality).tolist())  # add ranking to the school  list(range(schools.shape[0]))
        schools["school_ranking"] = rankings
        rankings_normalized = [1 - x / p["NUM_SCHOOLS"] for x in rankings]
        schools["school_quality_percentile"] = rankings_normalized
    return schools, p

"""
Parameters includes a vector of schools, along with features for each school.
Features can be a single value or a dictionary of values, mapping schools
to features. 

e.g., parameters["ADMISSION_FUNCTION"] = {"a": admission_function_a, "b": admission_function_b}
or parameters["ADMISSION_FUNCTION"] = admission_function
"""

def create_schools_market_fix_attributes(parameters):
    p = parameters
    school_names = p['SCHOOLS_LIST']
    
    school_features = ["SKILL_ESTIMATION_FUNCTION",
                       "CAPACITY",
                       "ADMISSION_FUNCTION",
                       "FEATURES_TO_USE",
                       #"SCHOOL_QUALITY",
                       ]
    schools = []
    for school_name in school_names:
        school = {}
        for feature in school_features:
            if type(p[feature])==dict:
                school[feature.lower().strip("skill_")] = p[feature][school_name] #feature is labeled "estimation_function" instead of "skill_estimation_function" in function calls
            else:
                school[feature.lower().strip("skill_")] = p[feature]
        if p["STUDENT_UTILITY"] is not None:
            school["school_quality"] = p["STUDENT_UTILITY"][school_name] #utility
        else:
            school["school_quality"] = get_school_quality(p, school_name)

        schools.append(school)
    schools = pd.DataFrame(schools)
    
    rankings = get_rank_of_each_item((-schools.school_quality).tolist())  # add ranking to the school  list(range(schools.shape[0]))
    schools["school_ranking"] = rankings
    rankings_normalized = [1 - x / p["NUM_SCHOOLS"] for x in rankings]
    schools["school_quality_percentile"] = rankings_normalized
    
    return schools, p

