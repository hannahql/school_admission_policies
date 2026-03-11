import pandas as pd
import os
import re, string
import hashlib

# pattern = re.compile('[\W_]+')
# pattern = re.compile('[.]')
from students.helpers import get_sampling_function


def get_empirical_feature_filename(num_features, parameters_distributions, path="schools/empiricalfeaturepdfs/"):
    strrs = []
    for feat in range(num_features):
        featurestr = [parameters_distributions["FEATURE_DIST_{}".format(feat)][0]]
        # featurestr.extend([pattern.sub('', '{:.5}'.format(float(x))) for x in parameters_distributions['FEATURE_DIST_{}'.format(feat)][1:]])
        featurestr.extend(["{:.5}".format(float(x)) for x in parameters_distributions["FEATURE_DIST_{}".format(feat)][1:]])

        strrs.append("".join(featurestr))
    joined = "_".join(strrs) + ".csv"
    if len(joined) > 70:  # just too long a file size...
        joined = hashlib.md5(joined.encode()).hexdigest()[0:20] + ".csv"
    return path + joined


def sample_save_features(num_students, num_features, parameters_distributions):
    filename = get_empirical_feature_filename(num_features, parameters_distributions)
    students = []
    p = parameters_distributions
    true_skill_sampling = get_sampling_function(p["TRUESKILL_DIST"])
    feature_samplings = []
    for feat in range(num_features):
        # p['FEATURE_DIST_{}'.format(feat)] = p['FEATURE_DIST_{}'.format(feat)] #idk why I had this line...
        feature_sampling = get_sampling_function(p["FEATURE_DIST_{}".format(feat)])
        feature_samplings.append(feature_sampling)
    for studnum in range(num_students):
        stud = {"skill": true_skill_sampling(0)}
        stud.update({"feature_{}".format(x): feature_samplings[x](stud["skill"]) for x in range(num_features)})
        students.append(stud)
    students = pd.DataFrame(students)

    if os.path.exists(filename):
        students_existing = pd.read_csv(filename)
        students = students.append(students_existing)
    students.to_csv(filename, index=False)


def load_features_qcut(num_features, parameters_distributions, qcuts=[1000, 500, 100, 50, 25, 10, 5]):
    bins = {}
    bin_labels = {}
    filename = get_empirical_feature_filename(num_features, parameters_distributions)
    print(filename)
    if os.path.exists(filename):
        print("file exists", filename)
        students_df = pd.read_csv(filename)
    else:
        print("sampling to create empirical q | theta", filename)
        sample_save_features(int(5e6), num_features, parameters_distributions)
        students_df = pd.read_csv(filename)
    # for each cut:
    # create the bins, add to a single pandas dataframe
    for cutnum in qcuts:
        for feature in range(num_features):
            students_df["feature{}_cut{}".format(feature, cutnum)], bins["feature{}_cut{}".format(feature, cutnum)] = pd.qcut(
                students_df["feature_{}".format(feature)], q=cutnum, duplicates="drop", retbins=True
            )
            bin_labels["feature{}_cut{}".format(feature, cutnum)] = list(
                students_df["feature{}_cut{}".format(feature, cutnum)].cat.categories
            )

    return students_df, bins, bin_labels
