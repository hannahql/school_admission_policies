import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
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
                                    sub_sub_results, 
                                    target_values,
                                    feature_to_vary = None
                                    ):
        
    # Filter the results DataFrame based on target values, excluding the feature to vary
    filtered_results = results_df.copy()
    #temp_sub_results = sub_sub_results.copy()
    for feature, value in target_values.items():
        filtered_results = filtered_results[filtered_results[feature] == value]
        #temp_sub_results = temp_sub_results[temp_sub_results[feature] == value]

    if feature_to_vary is not None:
        # # Calculate mean sub-sub results for the feature to vary
        # temp_sub_results = sub_sub_results.groupby(feature_to_vary).mean()
        
        #     # Calculate mean sub-sub results for the feature to vary
        # temp_sub_results = sub_sub_results.groupby(feature_to_vary).mean()
        


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
        
        temp_df_a = temp_df_a.append(
                               pd.Series({0:sub_sub_results['avgadmittedskill_school_a'].mean(),
                                      "Policy":"SUB_SUB"
                                      }, name=len(temp_df_a)))
        temp_df_b = temp_df_b.append(pd.Series({0:sub_sub_results['avgadmittedskill_school_b'].mean(),
                                        "Policy":"SUB_SUB"
                                        }, name=len(temp_df_b)))
                                     
    
    return temp_df_a, temp_df_b#, temp_sub_results

def plot_avg_admitted_skill_by_policy(
    results_df, 
    sub_sub_results, 
    feature_to_vary, 
    target_values
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

    # Calculate mean sub-sub results for the feature to vary
    temp_sub_results = sub_sub_results.groupby(feature_to_vary).mean()


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
