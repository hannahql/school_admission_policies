import numpy as np
import numpy.random as random
import json
import schools.estimation_functions_empirical_helpers as efeh

# iii. Empirical qtilde function that takes in a given set of features and indexes into the bins to find the empirical qtilde that matches it (maybe add a bit of noise so that ties are broken randomly)
# can do many different levels of estimation here…

group_to_empirical_df = {}
group_to_empirical_bins = {}
group_to_empirical_bin_labels = {}
groupqcut_to_bin_aggs = {}


def reset_globals():
    group_to_empirical_df = {}
    group_to_empirical_bins = {}
    group_to_empirical_bin_labels = {}
    groupqcut_to_bin_aggs = {}


def _generic_distribution_learning(
    student_features,
    group,
    features_to_use,
    parameters,
    qcuts=[1000, 900, 800, 700, 600, 500, 400, 350, 300, 275, 250, 200, 150, 125, 105, 100, 75, 50, 25, 10, 5],
    min_bin_count=20,
):
    global group_to_empirical_df
    global group_to_empirical_bins
    global group_to_empirical_bin_labels
    global groupqcut_to_bin_aggs

    parameters_group = {"TRUESKILL_DIST": parameters["TRUESKILL_DIST_{}".format(group)]}
    parameters_group.update(
        {"FEATURE_DIST_{}".format(feat): parameters["FEATURE_DIST_{}{}".format(group, feat)] for feat in range(len(student_features))}
    )
    grouphash = json.dumps(parameters_group, sort_keys=True)  # creates hash for the group parameters
    # map the student groups to the df of student samples using for empirical qtilde
    # if first student in that group, loading the right one, Otherwise load from the map
    if any(
        [
            grouphash not in group_to_empirical_df.keys(),
            grouphash not in group_to_empirical_bins.keys(),
            grouphash not in group_to_empirical_bin_labels.keys(),
        ]
    ):
        print(grouphash)
        (
            group_to_empirical_df[grouphash],
            group_to_empirical_bins[grouphash],
            group_to_empirical_bin_labels[grouphash],
        ) = efeh.load_features_qcut(len(student_features), parameters_group, qcuts=qcuts)
    emp_df = group_to_empirical_df[grouphash]
    bins = group_to_empirical_bins[grouphash]
    bin_labels = group_to_empirical_bin_labels[grouphash]

    # For the features of that student:
    # loop through the cut options, if the appropriate cut is big enough (>20), then choose that cut and grab the average q in that cut and treat it as qtilde
    for cutnum in qcuts:
        groupcutstr = "group{}_cut{}".format(grouphash, cutnum)
        featurestrs = ["feature{}_cut{}".format(feature, cutnum) for feature in range(len(student_features))]
        if groupcutstr not in groupqcut_to_bin_aggs.keys() or any(
            [x not in groupqcut_to_bin_aggs[groupcutstr].columns for x in featurestrs]
        ):
            # second part needed because what if the agg was created with fewer feautres bc of how a school does admissions
            # print('doing groupby', groupcutstr)
            groupqcut_to_bin_aggs[groupcutstr] = emp_df.groupby(featurestrs)["skill"].agg(["count", "mean"]).reset_index()
            # print('done with groupby')
        groupcutagg = groupqcut_to_bin_aggs[groupcutstr]

        for feature, featurecutstr in enumerate(featurestrs):
            # for each feature, get the appropriate bin for this observation
            # print(bins.keys())
            bin = np.digitize(student_features[feature], bins[featurecutstr])
            try:
                binlabel = bin_labels[featurecutstr][
                    int(min(max(0, bin - 1), len(bin_labels[featurecutstr]) - 1))
                ]  # edge cases if less than smallest bin or bigger than largest
            except Exception as e:
                print(e)
                print(student_features[feature])
                print(bins[featurecutstr])
                print(len(bins[featurecutstr]))
                print(bin_labels[featurecutstr])
                print(len(bin_labels[featurecutstr]))

                print(featurecutstr)
                print(max(0, bin - 1))
                print(cutnum)
                raise (e)
            groupcutagg = groupcutagg[groupcutagg[featurecutstr] == binlabel]
        # check the count for this bin, this qcut (and cache the count, remember global)
        # to get the right bin --- I can digitize for each feature to get the index. I need to convert that to the bin string (maybe do the sort in the loading and get the string labels), then look at the student_df then, can filter
        matching_bins = (
            groupcutagg[featurestrs].drop_duplicates().shape[0]
        )  # groupcutagg.groupby(featurestrs).ngroups #groupcutagg.shape[0] #should be 0 or 1
        # done by the group by because might not use all the features
        # print(matching_bins)
        if matching_bins > 1:
            print(matching_bins)
            print(groupcutagg.groupby(featurestrs))
            print(group, student_features)
            print(groupcutagg)
            print(groupcutstr)
            print(featurestrs)
            print(binlabel)
            print(cutnum)
        assert (matching_bins == 0) or (matching_bins == 1)
        if matching_bins == 1:  # there is a match...
            # # old way that didn't take into account that might not use all features
            #     # print(groupcutagg)
            #     matchrow = groupcutagg.iloc[0,:]
            #     count = matchrow['count']
            #     #if count above a certain value, can grab the mean skill in that bin and return (maybe add a tiny bit of noise)
            #     if count>=min_bin_count:
            #         # print(cutnum, end = ' ')
            #         return matchrow['mean'] + random.uniform(-1e-6, 1e-6)
            # new way
            count = groupcutagg["count"].sum()
            if count >= min_bin_count:
                # print(cutnum, end=" ")
                mean = (groupcutagg.eval("count * mean")).sum() / count
                return mean + random.uniform(-1e-6, 1e-6)


def genericdist_empirical_aware(row, features_to_use, parameters):
    group = row["group"]
    student_features = [row["feature_{}".format(feature)] for feature in range(parameters["NUM_FEATURES"] + features_to_use)]
    if any(np.isnan(student_features)):
        return np.nan

    return _generic_distribution_learning(student_features, group, features_to_use, parameters)
