import pandas as pd
import numpy as np
import ast
from collections import defaultdict

#Progress bar
from ipywidgets import IntProgress
from IPython.display import display


import pipeline


    
#Note - Saving and reading in data is a mess, since pandas changes the type of the data. 
def run_cost_model_different_costs(parameters, costs):
    parameters["SIMULATION_TYPE"] = "SINGLE_SCHOOL_COST_MODEL"
    params_by_cost = {}
    for c in costs:
        if isinstance(c, tuple):
            params_by_cost[c] = parameters.copy()
            params_by_cost[c]['STUDENT_TEST_COST'] = {"A":c[0], "B":c[1]}
        else:
            params_by_cost[c] = parameters.copy()
            params_by_cost[c]['STUDENT_TEST_COST'] = c
    students_dfs = {}
    schools_dfs = {}
    params_dfs = {}
    
    print(params_by_cost[c])
    
    # Progress Bar
    f = IntProgress(min=0, max=len(costs)) # instantiate the bar
    display(f) # display the bar
        
    for c in costs:
        students_df, schools_df, params_df = pipeline.pipeline(params_by_cost[c])
        students_dfs[c] = students_df
        schools_dfs[c] = schools_df
        params_dfs[c] = pd.Series(params_df)
        
        f.value += 1
        
    return students_dfs, schools_dfs, params_dfs





"""
The functions below are for reading in saved pandas dataframes,
when formats of columns are broken. 
"""

# Define the converter function
# For default dicts. 
def defaultdict_converter(defaultdict_string):
    try:
        # Removes default dict prefix
        dict_substring = defaultdict_string[defaultdict_string.index("{") : defaultdict_string.index("}")+1]
        
        # Convert the string to a dictionary
        dictionary = ast.literal_eval(dict_substring)
        return dictionary
    except (SyntaxError, ValueError):
        return defaultdict_string  # Return value as is if it cannot be converted
    
    
# Define the converter function
# Used for floats and dictionaries
def literal_converter(value):
    try:
        return ast.literal_eval(value)  # Convert string to dictionary
    except (SyntaxError, ValueError):
        return value  # Return value as is if it cannot be converted to a dictionary