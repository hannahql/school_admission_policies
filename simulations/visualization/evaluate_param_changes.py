import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

axis_label_map = {
    "frac": "Fraction of admitted",
    "CAPACITY": "Capacity",
    "FEATURE_DIST_B1_var": "Variance of test score for Group B",
    "FEATURE_DIST_B1_mean": "Mean of test score for Group B",
    "avgadmittedskill": "Average admitted skill",
    "FRAC_GROUPS_ADMIT_B": "$\\tau$, Diversity level",
    "school_quality_percentile": "School quality",
    "frac_B": "$\\tau$, Diversity level",
    "abovepoint5": "Avg. $I(q;P_{a,K})$ for $q\geq \mu$",
    "point8": "Avg. $I(q;P_{a,K})$ for $q\geq \mu$",
    "point84": "$I(q;P_{a,K})$ for $q=1$",
    "school_ranking_1": "School ranking",
    "PROB_MEETS_BUDGET_B": "Pr(Group B test access)",
}

group_labels = {"Group A": "Group A", "Group B": "Group B"}

sns.set_palette(sns.color_palette("cubehelix", 5))


def plot_group_features_by_param(df, label, y_param, x_param, school_type, groups=["A", "B"], legend=True, equivariance=None):
    sns.set_palette(sns.color_palette("cubehelix", len(groups)))
    dfloc = df.query('(school_type == "{}") and (label == "{}")'.format(school_type, label))
    ymin = 1000
    ymax = 0
    for group in groups:
        groupname = "Group {}".format(group)
        sns.lineplot(
            x=x_param,
            y="{}_{}".format(y_param, group),
            label=group_labels.get(groupname, groupname) if legend else None,
            data=dfloc,
            linewidth=2,
        )
        ymin = min(ymin, dfloc["{}_{}".format(y_param, group)].min())
        ymax = max(ymax, dfloc["{}_{}".format(y_param, group)].max())

    if legend:
        plt.legend(frameon=False, fontsize=17)
    if equivariance is not None:
        plt.vlines(x=equivariance, ymin=ymin, ymax=ymax, linewidth=2)
        plt.text(equivariance + 0.1, ymin * 1.05, "Equal precision", ha="left", va="center", fontsize=17)

    plt.xlabel(axis_label_map.get(x_param, x_param), size=20)
    plt.ylabel(axis_label_map.get(y_param, y_param), size=20)
    sns.despine()
    sns.set_palette(sns.color_palette("cubehelix", 5))


def plot_schools_by_param(df, label, y_param, x_param, school_types, school_labels, legend=True):
    sns.set_palette(sns.color_palette("cubehelix", len(school_types)))
    dflocc = df.query('(label == "{}")'.format(label))
    ymin = 1000
    ymax = 0
    for en, school in enumerate(school_types):
        dfloc = dflocc.query('(school_type == "{}")'.format(school))
        schoollab = school_labels[en]
        sns.lineplot(
            x=x_param,
            y="{}".format(y_param),
            label=schoollab if legend else None,
            data=dfloc,
            linewidth=2,
        )
        ymin = min(ymin, dfloc["{}".format(y_param)].min())
        ymax = max(ymax, dfloc["{}".format(y_param)].max())

    if legend:
        plt.legend(frameon=False, fontsize=17)

    plt.xlabel(axis_label_map.get(x_param, x_param), size=20)
    plt.ylabel(axis_label_map.get(y_param, y_param), size=20)
    sns.despine()
    sns.set_palette(sns.color_palette("cubehelix", 5))


def plot_feature_by_param(
    df, label, y_param, x_param, school_type, line_label=None, labelsize=20, equivariance=None, group_fairness=None, kind="line"
):
    dfloc = df.query('(school_type == "{}") and (label == "{}")'.format(school_type, label))
    if x_param == "school_ranking_1":
        dfloc = dfloc.dropna(subset=[x_param])
        dfloc["school_ranking_1"] = dfloc["school_ranking_1"].astype(int)
    print(dfloc.school_type.unique())
    # print(dfloc.head())
    if kind == "line":
        ax = sns.lineplot(x=x_param, y="{}".format(y_param), data=dfloc, label=line_label, linewidth=2)
    elif kind == "bar":
        ax = sns.barplot(x=x_param, y="{}".format(y_param), data=dfloc, label=line_label, linewidth=2, color=sns.color_palette()[4])
    plt.xlabel(axis_label_map.get(x_param, x_param), size=labelsize)
    plt.ylabel(axis_label_map.get(y_param, y_param), size=labelsize)
    if equivariance is not None:
        ymin = dfloc[y_param].min()
        ymax = dfloc[y_param].max()
        plt.vlines(x=equivariance, ymin=ymin, ymax=ymax, linewidth=2)
        plt.text(equivariance + 0.1, ymin + 0.05 * abs(ymin), "Equal precision", ha="left", va="center", fontsize=16)
    if group_fairness is not None:
        xmin = dfloc[x_param].min()
        xmax = dfloc[x_param].max()
        plt.hlines(y=group_fairness, xmin=xmin - 1.5, xmax=xmax - 0.25, linewidth=2)
        plt.text(xmin - 1.5, group_fairness + 0.025, "Group fairness", ha="left", va="center", fontsize=17)

    sns.despine()
    return ax
