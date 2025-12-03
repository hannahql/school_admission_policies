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

Runs all 4 policy combinations: SUB_SUB, SUB_FULL, FULL_SUB, FULL_FULL
For each parameter combination, all 4 policies share the same index.
"""

output_root = "simulation_data/NEW_mult_schools_simulations_policy_testing/"
n_processes = 16

# Generate all possible combinations of test policies (-1=SUB, 0=FULL)
test_policy_combinations = list(itertools.product([-1, 0], repeat=2))

# Create mapping for policy names
policy_names = {
    (-1, -1): "SUB_SUB",
    (-1, 0): "SUB_FULL", 
    (0, -1): "FULL_SUB",
    (0, 0): "FULL_FULL"
}




def run_simulation(args):
    """
    Function to run a single simulation with given parameters.
    
    Args:
        args: Tuple containing (idx, capacity_a, capacity_b, utility_a, utility_b, 
              test_cost, features_to_use_a, features_to_use_b, output_directory)
    """
    # Unpack all arguments
    idx, capacity_a, capacity_b, utility_a, utility_b, test_cost, features_to_use_a, features_to_use_b, output_directory = args
    
    #start_time = time.time()
    
    # Define base parameters with the policy-specific features
    base_parameters = {
        "SIMULATION_TYPE": "TWO_SCHOOL_COST_MODEL",
        "TRUESKILL_DIST": ("NORMAL", 0, 1),
        #"GRID_SEARCH_NUM_THRESHOLDS": 150,
        "GRID_SEARCH_NUM_THRESHOLDS": 10,
        "FEATURES_TO_USE_a": features_to_use_a,
        "FEATURES_TO_USE_b": features_to_use_b,
        #"NUM_STUDENTS": 1000,
        "NUM_STUDENTS": 100,
    }
    
    # Update the parameters with the current combination
    parameters_of_interest = {
        "CAPACITY_a": capacity_a,
        "CAPACITY_b": capacity_b,
        "STUDENT_UTILITY": {"a": utility_a, "b": utility_b},
        "STUDENT_TEST_COST": test_cost,
    }
    parameters = base_parameters.copy()
    parameters.update(parameters_of_interest)
    # print(f"Running with parameters: {parameters}")
    
    # Run the pipeline function with the current parameters
    students_df, schools_df, full_params = pipeline(parameters)
    
    # Save the DataFrames to CSV files
    students_df.to_csv(os.path.join(output_directory, f"students_df_{idx}.csv"), index=False)
    schools_df.to_csv(os.path.join(output_directory, f"schools_df_{idx}.csv"), index=False)
    
    # Save the parameters of interest to a JSON file
    with open(os.path.join(output_directory, f"parameters_of_interest_{idx}.json"), "w") as file:
        json.dump(parameters_of_interest, file, indent=4)

    # Save the full parameters to another JSON file
    with open(os.path.join(output_directory, f"full_parameters_{idx}.json"), "w") as file:
        json.dump(full_params, file, indent=4)
    
    #end_time = time.time()
    # print(f"{parameters_of_interest}: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    n_runs = 5
    
    # =============================================================================
    # Define parameter ranges to iterate over 
    # =============================================================================
    capacities_to_run_a = [0.2]
    capacities_to_run_b = [0.2]
    # utilities_to_run_a = [2, 3, 4,]
    # utilities_to_run_b = [1, 2, 3,]
    utilities_to_run_a = [3, 4]
    utilities_to_run_b = [2]

    # test_costs_to_run = [1.75,  2.0, 2.25]
    test_costs_to_run = [0.5, 1.5, 1.75, 2]
    
    # =============================================================================

    # Generate all combinations of parameters
    parameter_combinations = list(itertools.product(
        capacities_to_run_a,
        capacities_to_run_b,
        utilities_to_run_a,
        utilities_to_run_b,
        test_costs_to_run
    ))

    # Filter combinations where utility_a > utility_b
    valid_combinations = [
        (cap_a, cap_b, util_a, util_b, test_cost)
        for cap_a, cap_b, util_a, util_b, test_cost in parameter_combinations
        if util_a > util_b
    ]

    # Create output directories for all policies
    for features_to_use_a, features_to_use_b in test_policy_combinations:
        policy_name = policy_names[(features_to_use_a, features_to_use_b)]
        output_directory = os.path.join(output_root, f"{policy_name}_test/")
        os.makedirs(output_directory, exist_ok=True)
    
    # Build args list: for each parameter combination, run all 4 policies
    args_list = []
    for base_idx, (cap_a, cap_b, util_a, util_b, test_cost) in enumerate(valid_combinations):
        for run_num in range(n_runs):
            idx = base_idx + run_num * 100
            for features_to_use_a, features_to_use_b in test_policy_combinations:
                policy_name = policy_names[(features_to_use_a, features_to_use_b)]
                output_directory = os.path.join(output_root, f"{policy_name}_test/")
                
                args_list.append((
                    idx,  # Same index for all policies with same parameters
                    cap_a, cap_b, util_a, util_b, test_cost,
                    features_to_use_a, features_to_use_b,
                    output_directory
                ))
    
    # Run all simulations in parallel
    with Pool(n_processes) as pool:
        pool.map(run_simulation, args_list)

    print(f"Simulation complete. Results saved to {output_root}")
