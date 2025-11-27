
import pandas as pd
import numpy as np
from functools import partial
import matplotlib.pyplot as plt
import seaborn as sns

import os
import itertools
import json
import time

from multiprocessing import Pool

# Import my functions
from pipeline import pipeline


# from visualization.two_school_strategic_plots import (filter_results_by_target_values, 
#                                                       read_saved_inputs,
#                                                       plot_avg_admitted_skill_by_policy)

# n_processes = 16

min_index = 100

# main function
if __name__ == "__main__":
    fig_directory = "visualization/ms_revision_plots_2025_testing/"
    output_root = "simulation_data/mult_schools_simulations_policy_testing/"


    if not os.path.exists(fig_directory):
        os.makedirs(fig_directory)
        
    if not os.path.exists(output_root):
        os.makedirs(output_root)

    feature_name_map = {-1:"SUB", 0:"FULL"}
    
    # Generate all possible combinations of test policies (-1=SUB, 0=FULL)
    test_policy_combinations = list(itertools.product([-1, 0], repeat=2))

    # Create mapping for policy names
    policy_names = {
        (-1, -1): "SUB_SUB",
        (-1, 0): "SUB_FULL", 
        (0, -1): "FULL_SUB",
        (0, 0): "FULL_FULL"
    }

    for features_to_use_a, features_to_use_b in test_policy_combinations:
        # Create output root directory based on policy combination
        output_root = "simulation_data/mult_schools_simulations_policy_testing"

        output_directory = os.path.join(output_root, f"{policy_names[features_to_use_a, features_to_use_b]}_test/")
        #output_directory = "simulation_data/mult_schools_simulations_policy_SUB_SUB_test/"

        os.makedirs(output_directory, exist_ok=True)

        # Define your base parameters
        base_parameters = {
            "SIMULATION_TYPE": "TWO_SCHOOL_COST_MODEL",
            "TRUESKILL_DIST": ("NORMAL", 0, 1),
            "GRID_SEARCH_NUM_THRESHOLDS": 100,
            "FEATURES_TO_USE_a": features_to_use_a,
            "FEATURES_TO_USE_b": features_to_use_b,
            "NUM_STUDENTS":1000,
        }


        capacities_to_run_a = [0.2]
        capacities_to_run_b = [0.2]
        utilities_to_run_a = [2, 3, 4,]
        utilities_to_run_b = [1, 2, 3,]
        test_costs_to_run = test_costs_to_run = [0.5,  1.5, 2.0] #[1.75,  2.0, 2.25]

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
                #json.dump(all_parameters_of_interest, file, indent=4)

            # Optionally, save the full parameters to another JSON file
            with open(os.path.join(output_directory, f"full_parameters_{idx}.json"), "w") as file:
                json.dump(full_params, file, indent=4)
            end_time = time.time()
            print(f"{parameters_of_interest}: {end_time - start_time:.2f} seconds")
            return parameters_of_interest

        if __name__ == "__main__":
            with Pool() as pool:
                # num_processes = n_processes
                # Prepare arguments for each simulation
                args_list = [
                    (idx + min_index, capacity_a, capacity_b, utility_a, utility_b, test_cost)
                    for idx, (capacity_a, capacity_b, utility_a, utility_b, test_cost) in enumerate(valid_combinations)
                ]
                
                # Run simulations in parallel
                for result in pool.imap_unordered(run_simulation, args_list):
                    print(f"Completed simulation with parameters: {result}")

            print("Simulation complete. Results and parameters saved to files.")