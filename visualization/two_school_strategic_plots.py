import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os
import json




# Reading the saved inputs
def read_saved_inputs(index, output_directory):
    # Read the parameters of interest from a JSON file
    try:
        with open(os.path.join(output_directory, f"parameters_of_interest_{index}.json"), "r") as file:
            parameters_of_interest = json.load(file)
    except:
        with open(os.path.join(output_directory, "parameters_of_interest.json"), "r") as file:
            parameters_of_interest = json.load(file)
            parameters_of_interest = parameters_of_interest[index]

    # Read full parameters for a specific index
    with open(os.path.join(output_directory, f"full_parameters_{index}.json"), "r") as file:
        full_parameters = json.load(file)

    # Read the students DataFrame from a CSV file}
    students_df = pd.read_csv(os.path.join(output_directory, f"students_df_{index}.csv"))

    # Read the schools DataFrame from a CSV file
    schools_df = pd.read_csv(os.path.join(output_directory, f"schools_df_{index}.csv"))

    return parameters_of_interest, full_parameters, students_df, schools_df



def filter_results_by_target_values(results_df, 
                                    target_values,
                                    sub_sub_results=None, #whether to replace sub_sub results with passed in results
                                    feature_to_vary = None,
                                    return_mean_results=True, #if False, return individual rows
                                    ):
        
    # Filter the results DataFrame based on target values, excluding the feature to vary
    filtered_results = results_df.copy()

    if sub_sub_results is not None:
        filtered_sub_sub_results = sub_sub_results.copy()
    else:
        filtered_sub_sub_results = filtered_results.query("Policy == 'SUB_SUB_test'")
    

    for feature, value in target_values.items():
        # filtered_results = filtered_results[filtered_results[feature] == value]
        filtered_results = filtered_results.query(f"abs({feature} - @value) < 1e-3")
        
        if "COST" not in feature:
            filtered_sub_sub_results = filtered_sub_sub_results.query(f"abs({feature} - @value) < 1e-3")
        #temp_sub_results = temp_sub_results[temp_sub_results[feature] == value]

    if return_mean_results:
        # Take the mean in case there are multiple rows with the same parameter values# Take the mean in case there are multiple rows with the same parameter values
        group_cols = [col for col in filtered_results.columns 
                    if col not in ['avgadmittedskill_school_a', 
                                    'avgadmittedskill_school_b',
                                    'Index',
                                    'STUDENT_UTILITY']]
        group_cols_wo_cost = [col for col in group_cols if "COST" not in col]
        filtered_results = (filtered_results
                            .groupby(group_cols)
                            .mean(numeric_only=True)
                            .reset_index()
                            )

        filtered_sub_sub_results = (filtered_sub_sub_results
                                    .groupby(group_cols_wo_cost)
                                    .mean(numeric_only=True)
                                    .reset_index()
                                    )
        
    if feature_to_vary is not None:

        # Prepare data for School 1
        temp_df_a = (
            filtered_results
            #.query("Policy != 'SUB_SUB_nonstrategic_code'")
            [['Policy', 'avgadmittedskill_school_a', feature_to_vary]]
            .set_index(['Policy', feature_to_vary])
            .unstack(level=0)
        )
        
            # Prepare data for School 2
        temp_df_b = (
            filtered_results
            #.query("Policy != 'SUB_SUB_nonstrategic_code'")
            [['Policy', 'avgadmittedskill_school_b', feature_to_vary]]
            .set_index(['Policy', feature_to_vary])
            .unstack(level=0)
        )
    else: #target levels set for all features
        # Prepare data for School 1
        temp_df_a = (
            filtered_results
            #.query("Policy != 'SUB_SUB_nonstrategic_code'")
            [['Policy', 'avgadmittedskill_school_a']]
            .set_index(['Policy'])
            .unstack(level=0)
        )
        temp_df_a = temp_df_a.reset_index().drop(columns=["level_0"])
        
        # Prepare data for School 2
        temp_df_b = (
            filtered_results
            #.query("Policy != 'SUB_SUB_nonstrategic_code'")
            [['Policy', 'avgadmittedskill_school_b']]
            .set_index(['Policy'])
            .unstack(level=0)
        )
        temp_df_b = temp_df_b.reset_index().drop(columns=["level_0"])
        
    if sub_sub_results is not None:
        temp_df_a = temp_df_a.query("Policy != 'SUB_SUB_test'")
        temp_df_b = temp_df_b.query("Policy != 'SUB_SUB_test'")

        temp_df_a = pd.concat([temp_df_a, pd.DataFrame({
            "Policy": "SUB_SUB_test",
            0: filtered_sub_sub_results["avgadmittedskill_school_a"].values
        })], ignore_index=True)
        temp_df_b = pd.concat([temp_df_b, pd.DataFrame({
            "Policy": "SUB_SUB_test",
            0: filtered_sub_sub_results["avgadmittedskill_school_b"].values
        })], ignore_index=True)

        

        
        
                   
    # if sub_sub_results is not None: # add mean of SUB_SUB results passed in                
    #     temp_df_a = pd.concat(
    #     [
    #         temp_df_a,
    #         pd.DataFrame([{
    #             0: sub_sub_results['avgadmittedskill_school_a'].mean(),
    #             # 0: sub_sub_results['avgadmittedskill_school_a'],
    #             "Policy": "SUB_SUB"
    #         }])
    #     ],
    #     ignore_index=True
    #     )

    #     temp_df_b = pd.concat(
    #         [
    #             temp_df_b,
    #             pd.DataFrame([{
    #                 0: sub_sub_results['avgadmittedskill_school_b'].mean(),
    #                 # 0: sub_sub_results['avgadmittedskill_school_b'],
    #                 "Policy": "SUB_SUB"
    #             }])
    #         ],
    #         ignore_index=True
    #     )

        
    
    
    return temp_df_a, temp_df_b#, temp_sub_results


def plot_avg_admitted_skill_by_policy(
    results_df, 
    sub_sub_results, 
    feature_to_vary, 
    target_values,
):
    """
    Plots the average admitted skill by policy, varying a specified feature.

    :param results_df: DataFrame containing the results.
    :param sub_sub_results: DataFrame containing the sub-sub results.
    :param feature_to_vary: The feature to vary (e.g., 'UTILITY_a', 'UTILITY_b', 'STUDENT_TEST_COST').
    :param target_values: Dictionary of target values for other features to hold constant.
    """
    # Mapping for feature names to more descriptive labels
    feature_map = {
        "UTILITY_a": "Utility of School 1",
        "UTILITY_b": "Utility of School 2"
    }
    
    # Filter the results DataFrame based on target values, excluding the feature to vary
    filtered_results = results_df.copy()
    for feature, value in target_values.items():
        filtered_results = filtered_results[filtered_results[feature] == value]
    #print(filtered_results)

    if sub_sub_results is not None:
        filtered_sub_sub_results = sub_sub_results.copy()
        for feature, value in target_values.items():
            if "COST" not in feature:
                filtered_sub_sub_results = filtered_sub_sub_results[filtered_sub_sub_results[feature] == value]
        
    # # Calculate mean sub-sub results for the feature to vary
    # temp_sub_results = sub_sub_results.groupby(feature_to_vary).mean()


    # Prepare data for School 1
    temp_df_a = (
        filtered_results
        .query("Policy != 'SUB_SUB_nonstrategic_code'")
        [['Policy', 'avgadmittedskill_school_a', feature_to_vary]]
        .set_index(['Policy', feature_to_vary])
        .unstack(level=0)
    )
    temp_df_a.columns = temp_df_a.columns.droplevel(0)
    #print(temp_df_a)
    
    # Prepare data for School 2
    temp_df_b = (
        filtered_results
        .query("Policy != 'SUB_SUB_nonstrategic_code'")
        [['Policy', 'avgadmittedskill_school_b', feature_to_vary]]
        .set_index(['Policy', feature_to_vary])
        .unstack(level=0)
    )
    temp_df_b.columns = temp_df_b.columns.droplevel(0)
    
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 6), sharey=True)



    # Plot for School 1
    temp_df_a.plot(kind='bar', ax=axes[0])
    axes[0].axhline(temp_sub_results['avgadmittedskill_school_a'].mean(), 
                    color="red", label="SUB_SUB")
    axes[0].legend(loc=(0, 0))
    axes[0].set_title("School 1")
    axes[0].set_xlabel(feature_map.get(feature_to_vary, feature_to_vary))



    

    # Plot for School 2
    temp_df_b.plot(kind='bar', ax=axes[1])
    axes[1].axhline(temp_sub_results['avgadmittedskill_school_b'].mean(), 
                    color="red", label="SUB_SUB")
    axes[1].legend(loc=(1, 0))
    axes[1].set_title("School 2")
    axes[1].set_ylabel("Average Skill")
    axes[1].set_xlabel(feature_map.get(feature_to_vary, feature_to_vary))

    # Construct the title with fixed features and their values
    fixed_features = ", ".join([f"{feature_map.get(k, k)}: {v}" for k, v in target_values.items()])
    plt.suptitle(f"Average Admitted Skill by Policy and {feature_map.get(feature_to_vary, feature_to_vary)}\nFixed Features: {fixed_features}")
    plt.tight_layout()
    #plt.show()
    sns.despine()
    
    
def plot_avg_admitted_skill_by_policy_heatmap(
    results_df, 
    feature_to_vary, 
    target_values,
    fig_directory,
    sub_sub_results=None,
    plot_standard_errors=False,
):
    """
    Plots heatmap of the average admitted skill by policy, 
    varying a specified feature, and holding other features constant.
    
    If plot_standard_errors is True, the heatmap will be annotated
    with (mean ± 2 * SEM).
    """
    
    
    # Get mean results
    results_a, results_b = filter_results_by_target_values(
                                            results_df=results_df,
                                            sub_sub_results=sub_sub_results,
                                            feature_to_vary=feature_to_vary,
                                            target_values=target_values,
                                            return_mean_results=True,
                                            )


    # Extract the action parts from the policy names
    results_a['Action_A'] = results_a['Policy'].apply(lambda x: x.split('_')[0])
    results_a['Action_B'] = results_a['Policy'].apply(lambda x: x.split('_')[1])
    matrix_a = results_a.pivot(index='Action_A', columns='Action_B',
                            values=0)


    # Extract the action parts from the policy names
    results_b['Action_A'] = results_b['Policy'].apply(lambda x: x.split('_')[0])
    results_b['Action_B'] = results_b['Policy'].apply(lambda x: x.split('_')[1])
    matrix_b = results_b.pivot(index='Action_A', columns='Action_B',
                            values=0)
    
    if plot_standard_errors: # plot mean results and standard errors
        results_a_all, results_b_all = filter_results_by_target_values(
                                            results_df=results_df,
                                            sub_sub_results=sub_sub_results,
                                            feature_to_vary=feature_to_vary,
                                            target_values=target_values,
                                            return_mean_results=False,
                                            )
        sems_a = results_a_all.groupby("Policy").sem().reset_index()
        sems_b = results_b_all.groupby("Policy").sem().reset_index()

        
        sems_a['Action_A'] = sems_a['Policy'].apply(lambda x: x.split('_')[0])
        sems_a['Action_B'] = sems_a['Policy'].apply(lambda x: x.split('_')[1])
        sems_matrix_a = sems_a.pivot(index='Action_A', columns='Action_B',
                                    values=0)


        sems_b['Action_A'] = sems_b['Policy'].apply(lambda x: x.split('_')[0])
        sems_b['Action_B'] = sems_b['Policy'].apply(lambda x: x.split('_')[1])
        sems_matrix_b = sems_b.pivot(index='Action_A', columns='Action_B',
                                    values=0)
        
        # Create annotation strings for each cell
        annot_a = matrix_a.copy().astype(str)
        annot_b = matrix_b.copy().astype(str)

        for i in range(matrix_a.shape[0]):
            for j in range(matrix_a.shape[1]):
                val = matrix_a.iloc[i, j]
                try:
                    sem = sems_matrix_a.iloc[i, j]
                except Exception:
                    sem = np.nan
                if np.isnan(sem):
                    annot_a.iloc[i, j] = f"{val:.2f}"
                else:
                    annot_a.iloc[i, j] = f"{val:.2f}\n±{2*sem:.3f}"

        for i in range(matrix_b.shape[0]):
            for j in range(matrix_b.shape[1]):
                val = matrix_b.iloc[i, j]
                try:
                    sem = sems_matrix_b.iloc[i, j]
                except Exception:
                    sem = np.nan
                if np.isnan(sem):
                    annot_b.iloc[i, j] = f"{val:.2f}"
                else:
                    annot_b.iloc[i, j] = f"{val:.2f}\n±{2*sem:.3f}"
    
    # Create heatmap of matrix_a - avg admitted skill of school a
    # Create a figure with two subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    # Plot heatmap of matrix_a
    epsilon = 0.2
    vmin = min(matrix_a.min().min(), matrix_b.min().min()) - epsilon
    vmax = max(matrix_a.max().max(), matrix_b.max().max()) + epsilon
    if plot_standard_errors:
        sns.heatmap(matrix_a, annot=annot_a,  ax=ax1, vmin=vmin, vmax=vmax, 
                    cmap=sns.cm.rocket_r, annot_kws={"size": 18}, fmt=""
                    )
    else:
        sns.heatmap(matrix_a, annot=True, fmt='.3f', ax=ax1, vmin=vmin, vmax=vmax, 
                    cmap=sns.cm.rocket_r, annot_kws={"size": 18}) 
    ax1.set_title("Average admitted skill: $J_1$", fontsize=18, pad=20)
    ax1.xaxis.set_label_position('top')
    ax1.set_xlabel("$J_2$ policy", fontsize=18)
    ax1.xaxis.tick_top()
    ax1.set_ylabel("$J_1$ policy", fontsize=18)
    ax1.tick_params(axis='both', which='major', labelsize=18)



    # Plot heatmap of matrix_b - avg admitted skill of school b
    mask = matrix_b.isnull()
    if plot_standard_errors:
        sns.heatmap(matrix_b, annot=annot_b,  ax=ax2, vmin=vmin, vmax=vmax,
                    cmap=sns.cm.rocket_r, annot_kws={"size": 18}, fmt="",
                    )
    else:
        sns.heatmap(matrix_b, annot=True, fmt='.3f', ax=ax2, vmin=vmin, vmax=vmax,
                cmap=sns.cm.rocket_r, annot_kws={"size": 18}, mask=mask
                )
    # Get the colorbars from both heatmaps
    colorbar1 = ax1.collections[0].colorbar
    colorbar2 = ax2.collections[0].colorbar

    # Set font size for colorbar tick labels
    colorbar1.ax.tick_params(labelsize=14)
    colorbar2.ax.tick_params(labelsize=14)




    # # Customize the appearance of NA cells
    # Create a mask for NA values
    sns.heatmap(matrix_b, mask=~mask, cmap=['grey'], cbar=False, ax=ax2)
    # Annotate NaN cells with "NA"
    for i in range(matrix_b.shape[0]):
        for j in range(matrix_b.shape[1]):
            if mask.iloc[i, j]:
                ax2.text(j + 0.5, i + 0.5, 'NA', ha='center', va='center', color='black', fontsize=18)

    ax2.set_title("Average admitted skill: $J_2$", fontsize=18, pad=20)
    ax2.xaxis.set_label_position('top')
    ax2.xaxis.tick_top()
    ax2.set_xlabel("$J_2$ policy", fontsize=18)
    ax2.set_ylabel("$J_1$ policy", fontsize=18)
    ax2.tick_params(axis='both', which='major', labelsize=18)

    plt.subplots_adjust(wspace=10)

    plt.tight_layout()
    # INSERT_YOUR_CODE
    # Parse the names and values in target_values and append to the figure name
    if 'target_values' in locals() and hasattr(target_values, 'items'):
        target_kv_str = "_".join(f"{k}={v}" for k, v in sorted(target_values.items()))
    else:
        target_kv_str = "novals"
    plt.savefig(
        os.path.join(fig_directory, f"avg_skill_heatmap_{target_kv_str}{'_sems' if plot_standard_errors else ''}.png"),
        dpi=300
    )
    return
