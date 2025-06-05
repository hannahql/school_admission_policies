import pandas as pd
import numpy as np
from students.analytical_quantities_mult_schools import (q_underline_low_by_group, 
                                                         q_underline_high_by_group)

# Assuming students_df is your DataFrame and it has a 'group' column
def calculate_q_underline_values(row, schools_df, equilibrium_thresholds, parameters):
    # Extract the group of the student
    group = row['group']
    
    # Calculate q_underline_low and q_underline_high for the student's group
    q_underline_low = q_underline_low_by_group(group, schools_df, equilibrium_thresholds, parameters)
    q_underline_high = q_underline_high_by_group(group, schools_df, equilibrium_thresholds, parameters)
    
    # Return the calculated values
    return pd.Series({
        "q_underline_low": q_underline_low[group],
        "q_underline_high": q_underline_high[group]
    })
    
def add_q_underline_values_to_df(students_df, 
                                schools_df,
                                parameters
                                ):
    equilibrium_thresholds = {school_type: schools_df.loc[schools_df.school_type == school_type, "equil_threshold"].values[0] 
                              for school_type in schools_df.school_type.unique()}
    # Apply the function to each row in the students_df
    students_df[['q_underline_low', 'q_underline_high']] = students_df.apply(
        calculate_q_underline_values, 
        axis=1, 
        schools_df=schools_df, 
        equilibrium_thresholds=equilibrium_thresholds, 
        parameters=parameters
    )
    
    students_df["meet_low_bar"] = ( (schools_df['equil_threshold'][0]>=students_df["normal_learning_aware-1_score"]) 
                                    & (students_df["normal_learning_aware-1_score"]>= students_df["q_underline_low"])
    )
    max_values = np.maximum(students_df["q_underline_high"], schools_df['equil_threshold'][0])
    students_df["meet_high_bar"] = ( students_df["normal_learning_aware-1_score"] 
                                        >= max_values)
    students_df["meet_high_or_low_bar"] = (students_df["meet_low_bar"] | students_df["meet_high_bar"])
    
    students_df[students_df["meet_high_or_low_bar"]== students_df["take_test_at_thresholds_mult_schools"]]
    
def check_band_conditions(students_df, schools_df, parameters):
    equilibrium_thresholds = {school_type: schools_df.loc[schools_df.school_type == school_type, "equil_threshold"].values[0] 
                              for school_type in schools_df.school_type.unique()}
    students_df[['q_underline_low', 'q_underline_high']] = students_df.apply(
        calculate_q_underline_values, 
        axis=1, 
        schools_df=schools_df, 
        equilibrium_thresholds=equilibrium_thresholds, 
        parameters=parameters
    )
    
    
def theory_recommended_drop_decision(schools_df, parameters):
    pass
    
def add_theory_recommended_drop_decision_to_schools_df(schools_df, parameters):
    pass
    
