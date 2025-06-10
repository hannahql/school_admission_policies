import csv
import os
import pandas as pd

param_file_global = "params_run_paperclean5.csv"
schoolsdf_file_global = "run_metrics_schools_paperclean5.csv"


def set_save_files(label):
    global param_file_global
    global schoolsdf_file_global
    param_file_global = "params_run_{}.csv".format(label)
    schoolsdf_file_global = "run_metrics_schools_{}.csv".format(label)


def save_results_multiple(
    runlabel,
    runhashs,
    students_df_list,
    schools_df_list,
    parameters_list,
    param_file=param_file_global,
    schoolsdf_file=schoolsdf_file_global,
    current_param_df=None,
    current_metric_df=None,
    students_df_path="generated_data/",
):
    schools_all_df = pd.DataFrame()
    for en, _ in enumerate(parameters_list):
        parameters_list[en]["label"] = runlabel
        parameters_list[en]["hash"] = runhashs[en]

        schools_df_list[en].loc[:, "label"] = runlabel
        schools_df_list[en].loc[:, "hash"] = runhashs[en]

        save_students = parameters_list[en].get("save_students_df", False)

        if save_students:
            students_df_list[en].to_csv("{}{}__{}.csv".format(students_df_path, runlabel, runhashs[en]), index=False)
            schools_df_list[en]["admitted_students"] = list(schools_df_list[en]["admitted_students"])
        else:
            del schools_df_list[en]["admitted_students"]
        schools_all_df = schools_all_df.append(schools_df_list[en], ignore_index=True)


    if (current_param_df is not None) and (current_metric_df is not None):
        paramdf = current_param_df
        metricdf = current_metric_df
        paramdf = paramdf.append(pd.DataFrame(parameters_list), ignore_index=True)
        metricdf = metricdf.append(schools_all_df, ignore_index=True)
    elif os.path.exists(param_file):
        paramdf = pd.read_csv(param_file)
        paramdf = paramdf.append(pd.DataFrame(parameters_list), ignore_index=True)
        metricdf = pd.read_csv(schoolsdf_file)
        metricdf = metricdf.append(schools_all_df, ignore_index=True)
    else:
        paramdf = pd.DataFrame(parameters_list)
        metricdf = schools_all_df
    paramdf.to_csv(param_file, index=False)
    metricdf.to_csv(schoolsdf_file, index=False)

    return paramdf, metricdf


def load_results(param_file=param_file_global, schoolsdf_file=schoolsdf_file_global):
    paramdf = pd.read_csv(param_file)
    metricdf = pd.read_csv(schoolsdf_file)

    paramdf_eval_cols = [x for x in paramdf.columns if ("_DIST_" in x) or (x in ["FRACTIONS_GROUPS"])]

    def safeeval(x):
        if type(x) == str:
            return eval(x)
        return x

    for col in paramdf_eval_cols:
        paramdf.loc[:, col] = paramdf[col].apply(safeeval)

    del paramdf["label"]
    return metricdf.merge(paramdf, on="hash", how="left")
