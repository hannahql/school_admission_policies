import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import numpy as np
import copy
import os
import copy
from collections import defaultdict
import re
import ast  # Required to convert string representation of list to list
import itertools

from ipywidgets import IntProgress
from IPython.display import display

import save_results
import helpers
import pipeline
from pipeline_cost_run_multiple_instances import run_cost_model_different_costs, defaultdict_converter, literal_converter


def read_metric_from_schools_df(metric, schools_df, students_df, simulation_type):
    metric_value = schools_df[metric][0]
    
    return metric_value

def run_multiple_instances(instance_name, run_params, 
                           num_reps, simulation_data_path,
                            save_schools_df, save_students_df):
    
    metrics_df = defaultdict(dict)
    metrics = ['frac_A', 
            'avgadmittedskill']
    
    simulation_type = run_params["SIMULATION_TYPE"]
    instance_folder = simulation_data_path+instance_name+"/"
    os.makedirs(instance_folder, exist_ok=True)
    for i in range(num_reps):
        students_df, schools_df, params_df = pipeline.pipeline(run_params)
        params_df = pd.Series(params_df)
        
        if save_schools_df: schools_df.to_csv(instance_folder+"schools_df_{}.csv".format(i))
        if save_students_df: students_df.to_csv(instance_folder+"students_df_{}.csv".format(i))
        
        # Read metrics from df
        for metric in metrics:
            metrics_df[metric][i] = read_metric_from_schools_df(metric, schools_df, students_df,
                                                                simulation_type)
        
        
    for metric in metrics:
        metrics_df[metric] = pd.Series(metrics_df[metric])
        metrics_df[metric].to_csv(instance_folder+metric+".csv")
    
            
    ## SAVE PARAMS
    params_df.to_csv(instance_folder+"params_df.csv")
