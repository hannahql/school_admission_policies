import pandas as pd
import os
import re, string
import hashlib
from joblib import dump, load

# pattern = re.compile('[\W_]+')
# pattern = re.compile('[.]')
from students.helpers import get_sampling_function
from schools.estimation_functions_empirical_helpers import get_empirical_feature_filename


def get_model_filename(datafilename, num_features):
    return "{}{}.joblib".format(datafilename.replace(".csv", ""), num_features)


def train_model(students_df, num_features_valid):
    import patsy

    # from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression

    formula = "skill ~ {}".format(" + ".join(["feature_{}".format(x) for x in range(num_features_valid)]))
    y, X = patsy.dmatrices(formula, data=students_df)
    regr = LinearRegression()  # RandomForestRegressor(max_depth=5)
    # print(X)
    y = [yy[0] for yy in y]
    mod = regr.fit(X, y)
    return mod


def load_features_model(num_features, parameters_distributions):
    bins = {}
    bin_labels = {}
    datafilename = get_empirical_feature_filename(num_features, parameters_distributions)
    modelfilename = get_model_filename(datafilename, num_features)

    print(datafilename, modelfilename)
    if os.path.exists(datafilename):
        print("file exists", datafilename)
        students_df = pd.read_csv(datafilename)
    else:
        print("sampling to create empirical q | theta", datafilename)
        sample_save_features(int(5e6), num_features, parameters_distributions)
        students_df = pd.read_csv(datafilename)

    if os.path.exists(modelfilename):
        print("model exists", modelfilename)
        model = load(modelfilename)
    else:
        print("training model", modelfilename)
        model = train_model(students_df, num_features)
        dump(model, modelfilename)

    return model
