#!/apps/anaconda3/bin/python
import pandas as pd
import numpy as np
from functools import partial
import matplotlib.pyplot as plt


import os
import itertools
import json
import time

from multiprocessing import Pool


from pipeline import pipeline
from students.decision_functions_mult_schools import (
    exp_utility_mult_schools_test,
    exp_utility_mult_schools_no_test
)

"""
This script runs the two schools cost model (strategic students)
with varying test policies.

When running, update the output_directory and
features_to_use_a and features_to_use_b.
"""
output_directory = "simulation_data/mult_schools_simulations_policy_SUB_SUB_new_test_costs/"
features_to_use_a = -1
features_to_use_b = -1
n_processes = 16


os.makedirs(output_directory, exist_ok=True)

# Define base parameters
base_parameters = {
    "SIMULATION_TYPE": "TWO_SCHOOL_COST_MODEL",
    "TRUESKILL_DIST": ("NORMAL", 0, 1),
    "GRID_SEARCH_NUM_THRESHOLDS": 100,
    "FEATURES_TO_USE_a": features_to_use_a,
    "FEATURES_TO_USE_b": features_to_use_b,
    "NUM_STUDENTS":1000,
}

# Define parameter ranges to iterate over
capacities_to_run_a = [0.2]
capacities_to_run_b = [0.2]
utilities_to_run_a = [2, 3, 4,]
utilities_to_run_b = [1, 2, 3,]

test_costs_to_run = [1.75,  2.0, 2.25]

# Generate all combinations of parameters
parameter_combinations = itertools.product(
    capacities_to_run_a,
    capacities_to_run_b,
    utilities_to_run_a,
    utilities_to_run_b,
    test_costs_to_run
)

# Filter combinations where utility_a > utility_b
valid_combinations = [
    (cap_a, cap_b, util_a, util_b, test_cost)
    for cap_a, cap_b, util_a, util_b, test_cost in parameter_combinations
    if util_a > util_b
    if ((base_parameters["FEATURES_TO_USE_a"]==-1) 
        or (test_cost < util_a * (base_parameters["FEATURES_TO_USE_a"]+1))) # returns 1 if school a uses test

]


# Lists to store parameter sets
all_parameters_of_interest = []



def run_simulation(args):
    """Function to run a single simulation with given parameters."""
    idx, capacity_a, capacity_b, utility_a, utility_b, test_cost = args
    # Create a copy of the base parameters
    start_time = time.time()
    parameters = base_parameters.copy()
    
    # Update the parameters with the current combination
    parameters_of_interest = {
        "CAPACITY_a": capacity_a,
        "CAPACITY_b": capacity_b,
        "STUDENT_UTILITY": {"a": utility_a, "b": utility_b},
        "STUDENT_TEST_COST": test_cost,
    }
    parameters.update(parameters_of_interest)
    print(f"Running with parameters: {parameters}")
    
    # Run the pipeline function with the current parameters
    students_df, schools_df, full_params = pipeline(parameters)
    
    # Save the DataFrames to CSV files
    students_df.to_csv(os.path.join(output_directory, f"students_df_{idx}.csv"), index=False)
    schools_df.to_csv(os.path.join(output_directory, f"schools_df_{idx}.csv"), index=False)
    
    # Append the parameters of interest to the list
    all_parameters_of_interest.append(parameters_of_interest)
    
    # Save the parameters of interest to a JSON file after each iteration
    with open(os.path.join(output_directory, f"parameters_of_interest_{idx}.json"), "w") as file:
        json.dump(parameters_of_interest, file, indent=4)

    # Optionally, save the full parameters to another JSON file
    with open(os.path.join(output_directory, f"full_parameters_{idx}.json"), "w") as file:
        json.dump(full_params, file, indent=4)
    end_time = time.time()
    print(f"{parameters_of_interest}: {end_time - start_time:.2f} seconds")

# Use multiprocessing.Pool for parallel processing
if __name__ == "__main__":
    with Pool() as pool:
        num_processes = n_processes

        args_list = [
            (idx, capacity_a, capacity_b, utility_a, utility_b, test_cost)
            for idx, (capacity_a, capacity_b, utility_a, utility_b, test_cost) in enumerate(valid_combinations)
        ]
        
        # Run simulations in parallel
        pool.map(run_simulation, args_list)

    print("Simulation complete. Results and parameters saved to files.")
    
    

    