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

output_directory = "simulation_data/mult_schools_simulations_mult_runs/"
policies = [0, -1]
policy_combinations = itertools.product(policies, repeat=2)
policy_name_map = {0: "FULL", -1: "SUB"}

n_processes = 16
num_simulations = 16

os.makedirs(output_directory, exist_ok=True)

# Define base parameters
base_parameters = {
    "SIMULATION_TYPE": "TWO_SCHOOL_COST_MODEL",
    "TRUESKILL_DIST": ("NORMAL", 0, 1),
    "GRID_SEARCH_NUM_THRESHOLDS": 100,
    "NUM_STUDENTS":1000,
}

# Define parameter ranges to iterate over
#capacities_to_run_a = [0.1, 0.2, 0.3]
#capacities_to_run_b = [0.1, 0.2, 0.3]
capacity_to_run_a = 0.2
capacity_to_run_b = 0.2

utility_to_run_a = 3
utility_to_run_b = 2

test_cost_to_run = 2.0




# Lists to store parameter sets
all_parameters_of_interest = []






def run_simulation(args):
    """Function to run a single simulation with given parameters."""
    idx, capacity_a, capacity_b, utility_a, utility_b, test_cost, policy_a, policy_b, output_dir = args
    # Create a copy of the base parameters
    start_time = time.time()
    parameters = base_parameters.copy()
    
    # Update the parameters with the current combination
    parameters_of_interest = {
        "CAPACITY_a": capacity_a,
        "CAPACITY_b": capacity_b,
        "STUDENT_UTILITY": {"a": utility_a, "b": utility_b},
        "STUDENT_TEST_COST": test_cost,
        "FEATURES_TO_USE_a": policy_a,
        "FEATURES_TO_USE_b": policy_b,
    }
    parameters.update(parameters_of_interest)
    print(f"Run number: {idx}")
    
    # Run the pipeline function with the current parameters
    students_df, schools_df, full_params = pipeline(parameters)
    
    # Save the DataFrames to CSV files
    students_df.to_csv(os.path.join(output_dir, f"students_df_{idx}.csv"), index=False)
    schools_df.to_csv(os.path.join(output_dir, f"schools_df_{idx}.csv"), index=False)
    
    # Append the parameters of interest to the list
    all_parameters_of_interest.append(parameters_of_interest)
    
    # Save the parameters of interest to a JSON file after each iteration
    with open(os.path.join(output_dir, f"parameters_of_interest_{idx}.json"), "w") as file:
        json.dump(parameters_of_interest, file, indent=4)
        #json.dump(all_parameters_of_interest, file, indent=4)

    # Optionally, save the full parameters to another JSON file
    with open(os.path.join(output_dir, f"full_parameters_{idx}.json"), "w") as file:
        json.dump(full_params, file, indent=4)
    end_time = time.time()
    print(f"{parameters_of_interest}: {end_time - start_time:.2f} seconds")

# Use multiprocessing.Pool for parallel processing
if __name__ == "__main__":
    for policy_a, policy_b in policy_combinations:
        output_dir = os.path.join(output_directory, f"{policy_name_map[policy_a]}_{policy_name_map[policy_b]}")
        os.makedirs(output_dir, exist_ok=True)
        
        with Pool() as pool:
            num_processes = n_processes

            args_list = [
                (idx, capacity_to_run_a, capacity_to_run_b, utility_to_run_a, utility_to_run_b, 
                 test_cost_to_run, policy_a, policy_b, output_dir)
                for idx in range(num_simulations)
            ]
            
            # Run simulations in parallel
            pool.map(run_simulation, args_list)

    print("Simulation complete. Results and parameters saved to files.")
    
    

    