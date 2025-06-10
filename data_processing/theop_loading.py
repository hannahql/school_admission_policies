import pandas as pd
import numpy as np

data_folder = "../data/theop/"
univ_names = {
    "am": "Texas A&M",
    "amk": "Texas A&M Kingsville",
    "ar": "UT Arlington",
    "au": "UT Austin",
    "pa": "UT Pan American",
    # "sa": "UT San Antonio", # NOTE I don't know why this is commented out. Looks like we don't have data for UTSA
    "tt": "Texas Tech",
    "ri": "Rice",
    "sm": "Southern Methodist",
}

decile_map = {
    "Top 10%": 0.9,
    "Second Decile": 0.8,
    "Third Decile": 0.7,
    "Fourth Decile": 0.6,
    "Fifth Decile": 0.5,
    "Sixth Decile": 0.4,
    "Seventh Decile or Below": 0.3,
}

hseconstatus_map = {"Upper quartile": 0.75, "Upper-middle quartile": 0.5, "Lower-middle quartile": 0.25, "Lower quartile": 0}


def load_theop_files(names=univ_names.keys(), whichones="applications"):
    dfs = []
    for name in names:
        df = pd.read_stata("{}theop_{}_college_{}.dta".format(data_folder, name, whichones))
        df.loc[:, "studentid"] = name + df["studentid"]
        df.loc[:, "instcode"] = name
        df.loc[:, "institution"] = univ_names[name]
        dfs.append(df)
    return pd.concat(dfs)


def load_application_files(names=univ_names.keys()):
    return load_theop_files(names=names, whichones="applications")


def load_transcript_files(names=univ_names.keys()):
    df = load_theop_files(names=names, whichones="transcripts")
    # df = df.drop_duplicates(keep="first", subset=["studentid"])
    return df


def load_and_join_theop_files(names=univ_names.keys()):
    apps = load_application_files(names)
    transcripts = load_transcript_files(names)
    return apps.merge(transcripts, how="left", on="studentid", suffixes=("", "_y"))


def process_test_score(df, col):
    newcol = "{}_clean".format(col)
    f = lambda d: np.mean([float(x) for x in d]) if type(d) is list else np.nan
    df.loc[:, newcol] = (
        df[col].str.replace("Less than ", "").str.replace(" or more", "").str.split("-").apply(f)
    )  # , expand=True).mean(axis = 1).astype(float)
    return df


def get_mean_cgpa_per_field(df, colgroup="term_major_field", col="cgpa_overall"):
    means = df.groupby(colgroup)[col].mean().reset_index()
    means = means.rename(columns={col: "{}_{}_mean".format(colgroup, col)})
    df = df.merge(means, how="left", on=colgroup)
    return df


def process_transcripts_to_get_firstlastgpa(dft):
    dft = process_test_score(dft, "hrearn")
    dft = process_test_score(dft, "semgpa")
    dft.loc[:, "gpahours"] = dft.eval("hrearn_clean * semgpa_clean")
    dft.loc[:, "chrearn"] = dft.groupby("studentid")["hrearn_clean"].transform(pd.Series.cumsum)
    dftover24hours = dft.query("chrearn>=24")
    dftfirstyear = dftover24hours.drop_duplicates(subset=["studentid"], keep="first")

    def mask_first(x):  # get rid of first row of each group -- since using that first row to get first year gpa.
        result = np.ones_like(x)
        result[0] = 0
        return result

    mask = dftover24hours.groupby(["studentid"])["studentid"].transform(mask_first).astype(bool)
    dftrest = dftover24hours[mask]
    dftrest.loc[:, "chrearn"] = dftrest.groupby("studentid")["hrearn_clean"].transform(pd.Series.cumsum)
    dftrest.loc[:, "cgpahours"] = dftrest.groupby("studentid")["gpahours"].transform(pd.Series.cumsum)
    dftrest = dftrest.drop_duplicates(subset=["studentid"], keep="last")

    dftrest.loc[:, "cgpa_overall"] = dftrest.loc[:, "cgpa"]
    dftrest = get_mean_cgpa_per_field(dftrest)

    dftrest.loc[:, "cgpa"] = dftrest.eval("cgpahours/chrearn")
    dftfirstyear = dftfirstyear[
        ["studentid", "instcode", "institution", "year", "term", "cgpa", "chrearn", "term_major_dept", "term_major_field"]
    ]
    dftrest = dftrest[
        [
            "studentid",
            "year",
            "term",
            "cgpa",
            "cgpa_overall",
            "chrearn",
            "term_major_dept",
            "term_major_field",
            "term_major_field_cgpa_overall_mean",
        ]
    ]
    dft_withscores = dftfirstyear.merge(dftrest, how="left", on="studentid", suffixes=["_firstyear", "_finalnotfirst"])
    return dft_withscores


def process_applications(dfa):
    dfa = process_test_score(dfa, "testscoreR")
    dfa.loc[:, "decileR"] = dfa.loc[:, "decileR"].replace(decile_map)
    # dfa = process_test_score(dfa, 'satR')
    # dfa = process_test_score(dfa, 'actR')
    dfa = dfa[
        [
            "studentid",
            "instcode", #added 10/2/2022 when doing empirical stuff
            "institution", #added 10/2/2022 when doing empirical stuff
            "yeardes",
            "termdes",
            "male",
            "ethnic",
            # "citizenship", #not there for all schools, not using
            # "restype", #not there for all schools, not using
            "decileR",
            "major_field",
            "hsprivate",
            "hstypeR",
            "hsinstate",
            "hseconstatus",
            "admit",
            "enroll",
            "gradyear",
            "testscoreR_clean",
        ]
    ]
    dfa = dfa.rename(columns={"testscoreR_clean": "testscore"})
    dfa.loc[:, "hseconstatus"] = dfa.loc[:, "hseconstatus"].replace(hseconstatus_map)
    return dfa


def load_and_process_applications_transcripts(names=univ_names):
    dft = load_transcript_files(names)
    dft = process_transcripts_to_get_firstlastgpa(dft)
    dfa = load_application_files(names)
    dfa = process_applications(dfa)
    df = dfa.merge(dft, how="left", on="studentid", suffixes=["_apply", ""])
    return df
