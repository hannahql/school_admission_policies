import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

from visualization.evaluate_param_changes import *
from generic.latexify import *
from generic.helpers import eval_list

school_names_pretty = {
    "a": "Aware estimation, test-based",
    "b": "Unaware estimation, test-based",
    "d": "Aware estimation, test-free",
    "e": "Unaware estimation, test-free",
    "c": "Aware estimation, affirmative action level $\\tau=.5$, test-based",
    "f": "Aware estimation, affirmative action level $\\tau=.5$, test-free",
}


school_names_pretty_pnas = {
    "a": "Test-based\nw/o Aff. Action",
    "b": "Test-based\n Unaware\n estimation",
    "d": "Test-free\nw/o Aff. Action",
    "e": "Test-free\n Unaware\n estimation",
    "c": "Affirmative action level $\\tau=.5$, Test-based",
    "f": "Affirmative action level $\\tau=.5$, Test-free",
}

school_names_notation_pnas = {
    "a": "$P_{K}$",
    "b": "$P_{K}$",
    "d": "$P_{K-1}$",
    "e": "$P_{K-1}$",
    "c": "$P_{K}^{0.5}$",
    "f": "$P_{K-1}^{0.5}$",
}

school_names_notation = {
    "a": "$P_{a,K}$",
    "b": "$P_{u,K}$",
    "d": "$P_{a,K-1}$",
    "e": "$P_{u,K-1}$",
    "c": "$P_{a,K}^{0.5}$",
    "f": "$P_{a,K-1}^{0.5}$",
}

group_names_pretty = {"A": "Group A", "B": "Group B"}
schoolorder_default = list(sorted(school_names_pretty.keys()))

# offsets_default = {"a": [-0.5, 0.1], "b": [-0.05, 0.1], "d": [-0.3, -0.05], "e": [-0.05, -0.05], "c": [-0.48, 0.05], "f": [0.05, 0.01]}
offsets_default = {"a": [-0.05, 0.045], "b": [-0.15, 0.17], "d": [-0.05, -0.10], "e": [-0.05, -0.2], "c": [0.03, 0.025], "f": [0, -0.06]}


def format_heatmap_ticklabel(text, precision):
    try:
        return ("{:0." + str(precision) + "f}").format(float(text))
    except (TypeError, ValueError):
        return text


def plot_multiple_pareto_points_clean(
    dff,
    label,
    school_names=school_names_pretty_pnas,
    school_names_notation=school_names_notation_pnas,
    offsets=offsets_default,
    schools_todo=None,
    savenameappend="",
    arrows=False,
):
    sns.set_palette(sns.color_palette("cubehelix", 2))

    if schools_todo is None:
        schools_todo = school_names_pretty.keys()
    dfloc = dff.query('(label == "{}")'.format(label))
    avgbyschool = dfloc.groupby("school_type")[["avgadmittedskill", "frac_B"]].mean()
    print(dfloc.school_type.unique())

    pointdict = {}
    offsets = {school_names[school]: offsets[school] for school in offsets.keys()}
    for school in ["a", "b", "d", "e"]:
        if school not in schools_todo:
            continue
        pointdict[school] = list(avgbyschool.loc[school])[::-1]
    for school in ["c", "f"]:
        if school not in schools_todo:
            continue
        demoparity_mean = dfloc.query("school_type==@school and frac_B>=.49 and frac_B<=.51")["avgadmittedskill"].mean()
        if np.isnan(demoparity_mean):
            continue
        pointdict[school] = [0.5, demoparity_mean]
    print(pointdict)
    ax = plot_feature_by_param(
        dff,
        label=label,
        y_param="avgadmittedskill",
        x_param="FRAC_GROUPS_ADMIT_B",
        school_type="c",
        line_label="Test-based w/ Aff. Action level $\\tau$",
        labelsize=20,
    )

    plot_feature_by_param(
        dff,
        label=label,
        y_param="avgadmittedskill",
        x_param="FRAC_GROUPS_ADMIT_B",
        school_type="f",
        line_label="Test-free w/ Aff. Action level $\\tau$",
        labelsize=20,
    )
    plt.legend(frameon=False)
    plt.scatter([pointdict[x][0] for x in pointdict], [pointdict[x][1] for x in pointdict], s=30, c="k")

    for en, x in enumerate(sorted(pointdict.keys())):
        ax.annotate(
            # "{}: {}".format(school_names_notation[x], school_names[x]),
            "{1}".format(school_names_notation[x], school_names[x]),
            pointdict[x],
            size=15,
            xytext=(pointdict[x][0] + offsets[school_names[x]][0], pointdict[x][1] + offsets[school_names[x]][1]),
            # xytext=(pointdict[x][0], pointdict[x][1] + 0.025),
            arrowprops=[None, dict(facecolor="black", shrink=0.05)][arrows],
        )

    saveimage("{}_{}{}".format(label, "differentpoliciescurves", savenameappend), close=False)
    sns.set_palette(sns.color_palette("cubehelix", 5))


def plot_multiple_pareto_points(dff, label, school_names=school_names_pretty, offsets=offsets_default, schools_todo=None):
    sns.set_palette(sns.color_palette("cubehelix", 2))

    if schools_todo is None:
        schools_todo = school_names_pretty.keys()
    dfloc = dff.query('(label == "{}")'.format(label))
    avgbyschool = dfloc.groupby("school_type")[["avgadmittedskill", "frac_B"]].mean()
    print(dfloc.school_type.unique())

    pointdict = {}
    offsets = {school_names[school]: offsets[school] for school in offsets.keys()}
    for school in ["a", "b", "d", "e"]:
        if school not in schools_todo:
            continue
        pointdict[school] = list(avgbyschool.loc[school])[::-1]
    for school in ["c", "f"]:
        if school not in schools_todo:
            continue
        demoparity_mean = dfloc.query("school_type==@school and frac_B>=.49 and frac_B<=.51")["avgadmittedskill"].mean()
        if np.isnan(demoparity_mean):
            continue
        pointdict[school] = [0.5, demoparity_mean]
    print(pointdict)
    ax = plot_feature_by_param(
        dff,
        label=label,
        y_param="avgadmittedskill",
        x_param="FRAC_GROUPS_ADMIT_B",
        school_type="c",
        line_label="$P_{a,K}^{\\tau}$",
        labelsize=20,
    )
    plot_feature_by_param(
        dff,
        label=label,
        y_param="avgadmittedskill",
        x_param="FRAC_GROUPS_ADMIT_B",
        school_type="f",
        line_label="$P_{a,K-1}^{\\tau}$",
        labelsize=20,
    )
    plt.legend(frameon=False)
    plt.scatter([pointdict[x][0] for x in pointdict], [pointdict[x][1] for x in pointdict], s=30, c="k")

    for en, tt in enumerate(
        [
            "$P_{a,K}^{\\tau}$: Aware estimation, affirmative action level $\\tau$, test-based",
            "$P_{a,K-1}^{\\tau}$: Aware estimation, affirmative action level $\\tau$, test-free",
        ]
    ):
        plt.text(
            0.05,
            -0.07 + (en) * -0.07,
            tt,
            fontsize=14,
            transform=plt.gcf().transFigure,
        )

    for en, x in enumerate(sorted(pointdict.keys())):
        ax.annotate(
            school_names_notation[x],
            pointdict[x],
            size=15,
            xytext=(pointdict[x][0] + offsets[school_names[x]][0], pointdict[x][1] + offsets[school_names[x]][1]),
            # xytext=(pointdict[x][0], pointdict[x][1] + 0.025),
            # arrowprops=dict(facecolor="black", shrink=0.05),
        )
        plt.text(
            0.05,
            -0.07 + (2 + en) * -0.07,
            "{}: {}".format(school_names_notation[x], school_names[x]),
            fontsize=14,
            transform=plt.gcf().transFigure,
        )

    saveimage("{}_{}".format(label, "differentpoliciescurves"), close=False)
    sns.set_palette(sns.color_palette("cubehelix", 5))


def plot_estimate_thresholds(school_type, schools_df, students_df, label, bins=10, kde=True):
    sns.set_palette(sns.color_palette("cubehelix", 2))
    school_row = schools_df.query('school_type =="{}"'.format(school_type)).iloc[0]
    score_str = "{}{}_score".format(school_row.estimation_function, school_row.features_to_use)
    school_threshold = students_df.iloc[school_row.admitted_students][score_str].min()

    if kde:
        g = sns.kdeplot(x=score_str, data=students_df, hue="group", fill=True)  # , kde = True)
        ymax = 0.4
        ylabel = "Pr$(\\tilde q(\eta, g))$"
        plt.yticks([])
    else:
        g = sns.histplot(x=score_str, data=students_df, hue="group", element="step", bins=bins)
        ymax = 1000
        ylabel = "Count"

    plt.legend(title="", loc="upper left", labels=["Group B", "Group A"], frameon=False, fontsize=15)
    sns.despine()
    plt.vlines(x=school_threshold, ymin=0, ymax=ymax, linewidth=2)
    plt.text(school_threshold + 0.1, ymax * 0.7, "Admissions \n threshold", ha="left", va="center", fontsize=15)
    plt.xlabel("Skill estimate $\\tilde q(\eta, g)$", fontsize=20)
    plt.ylabel(ylabel, fontsize=20)
    teststrlabel = "free" if school_row.features_to_use == -1 else "based"
    saveimage("{}_skilldist_test{}".format(label, teststrlabel), close=False)
    sns.set_palette(sns.color_palette("cubehelix", 5))


def plot_2dheatmap_diff(
    dff,
    label,
    x="FEATURE_DIST_B1_var",
    y="PROB_MEETS_BUDGET_B",
    z="frac_B",
    vmin=None,
    vmax=None,
    cmap=sns.color_palette("vlag_r", as_cmap=True),
    schools=["a", "b"],
    y_min=None,
):

    axis_label_map_loc = {
        "FEATURE_DIST_B1_var": "Variance of test score",
        "avgadmittedskill": "Average admitted skill",
        "PROB_MEETS_BUDGET_B": "Pr(Group B test access)",
    }

    firstype, secondtype = schools
    dffloca = dff.query("label == @label and school_type==@firstype")
    if y_min is not None:
        dffloca = dffloca[dffloca[y] >= y_min]
    dfffa = dffloca.groupby([x, y])[z].mean().reset_index()
    dfflocb = dff.query("label == @label and school_type==@secondtype")
    if y_min is not None:
        dfflocb = dfflocb[dfflocb[y] >= y_min]
    dfffb = dfflocb.groupby([x, y])[z].mean().reset_index()

    piva = dfffa.pivot(index=x, columns=y, values=z)
    pivb = dfffb.pivot(index=x, columns=y, values=z)
    p = piva - pivb
    # print(min(p), max(p))
    ax = sns.heatmap(p, cmap=cmap, vmin=vmin, vmax=vmax, xticklabels=2, yticklabels=2)
    ax.invert_yaxis()

    xticks = ax.get_xticks()
    yticks = ax.get_yticks()
    ax.set_xticks(xticks)
    ax.set_yticks(yticks)
    ax.set_xticklabels([format_heatmap_ticklabel(label.get_text(), 2) for label in ax.get_xticklabels()])
    ax.set_yticklabels([format_heatmap_ticklabel(label.get_text(), 2) for label in ax.get_yticklabels()])

    # fmt = "{:0.2f}"
    # xticklabels = []
    # for item in ax.get_xticklabels():
    #     item.set_text(fmt.format(float(item.get_text())))
    #     xticklabels += [item]
    # yticklabels = []
    # for item in ax.get_yticklabels():
    #     item.set_text(fmt.format(float(item.get_text())))
    #     yticklabels += [item]
    # ax.set_xticklabels(xticklabels)
    # ax.set_yticklabels(yticklabels)

    plt.ylabel(axis_label_map_loc.get(x, x), size=30)
    plt.xlabel(axis_label_map_loc.get(y, y), size=30)
    sns.despine()
    saveimage("{}_2ddifference_{}".format(label, z), close=False)
    return p


def plot_2d_estimate_thresholds(
    school_type,
    schools_df,
    students_df,
    label,
    bins=10,
    kde=True,
    numeach=20000,
    ymin=-3,
    ymax=3,
    ylabel="True skill $q$",
    xlabel="Skill estimate $\\tilde q(\eta, g)$",
    scale_kdw=1,
    do_legend=False,
    skillline="Avg. Admitted\nskill",
    decimals=1,
    textdistmult=1,
    textfontsize=22,
    for_presentation=False,
    num_groups=2,
    do_admitted=True,
):
    # sns.set_palette()
    pal = sns.color_palette("cubehelix", 2)
    school_row = schools_df.query('school_type =="{}"'.format(school_type)).iloc[0]
    score_str = "{}{}_score".format(school_row.estimation_function, school_row.features_to_use)
    school_threshold = students_df.iloc[school_row.admitted_students][score_str].min()

    fracGroupB = (students_df.iloc[school_row.admitted_students]["group"] == "B").mean() * 100
    avgskill = (students_df.iloc[school_row.admitted_students]["skill"]).mean()

    maj = students_df[students_df.group == "A"].sample(numeach)
    dis = students_df[students_df.group == "B"].sample(numeach)

    if num_groups == 1:
        students_df = pd.concat([maj])
        pal = sns.color_palette("cubehelix", 1)
        palette = {"Group A": pal[0], "fake": "white"}

    else:
        students_df = pd.concat([maj, dis])
        palette = {"Group A": pal[0], "Group B": pal[1], "fake": "white"}

    students_df["group"] = students_df.group.replace("A", "Group A")
    students_df["group"] = students_df.group.replace("B", "Group B")

    # students_fake_for_scale = pd.DataFrame(
    #     {
    #         "skill": np.random.normal(size=numeach * scale_kdw),
    #         score_str: np.random.normal(scale=0.5, size=numeach * scale_kdw),
    #         "group": ["fake" for _ in range(numeach * scale_kdw)],
    #     }
    # )

    levels = 5

    students_df.loc[students_df[score_str].isna(), "skill"] = np.nan
    # students_df = pd.concat([students_df, students_fake_for_scale])

    g = sns.jointplot(
        y="skill",
        x=score_str,
        data=students_df,
        hue="group",
        kind="kde",
        fill=True,
        alpha=0.2,
        levels=levels,
        palette=palette,
    )
    # g = sns.jointplot(
    #     palette={"Group A": pal[0], "Group B": pal[1], "fake": "white"},
    #     # marginal_kws=dict(ylim=(0, 2)),
    # )  # , kde = True)
    # "Pr$(\\tilde q(\eta, g))$"
    #         plt.yticks([])

    g.plot_joint(sns.kdeplot, zorder=0, levels=levels)
    plt.legend(frameon=False)
    ax = plt.gca()
    #     legend = ax.legend()
    #     legend.get_frame().set_facecolor('none')
    #     ax.legend(labels=["Group B", "Group A"], frameon = False, title = None)
    #     plt.legend(frameon = False)
    #     ax.legend(loc="upper left", labels=["Group B", "Group A"], frameon=False, fontsize=15)
    sns.despine()
    #     g.set_axis_labels()

    if not for_presentation:
        plt.text(
            ymin + 0.1 * textdistmult,
            ymax - 0.25 * textdistmult,
            "$\%$ Admitted\nGroup B: {:.1f}".format(fracGroupB),
            ha="left",
            va="center",
            fontsize=textfontsize,
        )
        plt.text(
            ymin + 0.1 * textdistmult,
            ymax - 1.5 * textdistmult,
            ("{}: {:." + str(decimals) + "f}").format(skillline, avgskill),
            ha="left",
            va="center",
            fontsize=textfontsize,
        )
    else:
        xlabel = "Skill estimate $\\tilde q(\\theta, g)$"

    if do_admitted:
        plt.text(
            school_threshold + 0.1 * textdistmult,
            ymin + 0.4 * textdistmult,
            "Admitted\nstudents",
            ha="left",
            va="center",
            fontsize=textfontsize,
        )
        plt.vlines(x=school_threshold, ymin=ymin, ymax=ymax, linewidth=2)
        plt.axvspan(school_threshold, ymax, alpha=0.1, color="black")
    plt.xlabel(xlabel, fontsize=30)
    plt.ylabel(ylabel, fontsize=30)
    teststrlabel = "free" if school_row.features_to_use == -1 else "based"
    plt.xlim((ymin, ymax))
    plt.ylim((ymin, ymax))
    plt.plot(np.linspace(ymin, ymax, 100), np.linspace(ymin, ymax, 100), "--", c="k")
    # plt.text(ymin + 0.4, ymin + 0.25, "Perfect estimation", ha="left", va="center", fontsize=15)

    # g.ax_marg_x.hist(
    # students_df[score_str], kde=True, hue="group", palette={"Group A": pal[0], "Group B": pal[1], "fake": "white"}
    # )
    # g.ax_marg_y.hist(bins=np.arange(-3, 3, 5))

    g.ax_marg_x.set_xlabel("")
    g.ax_marg_x.set_ylabel("")
    g.ax_marg_y.set_xlabel("")
    g.ax_marg_y.set_ylabel("")
    for marginal_ax in [g.ax_marg_x, g.ax_marg_y]:
        marginal_ax.tick_params(
            axis="both",
            which="both",
            bottom=False,
            top=False,
            left=False,
            right=False,
            labelbottom=False,
            labeltop=False,
            labelleft=False,
            labelright=False,
        )

    from matplotlib.patches import Patch

    if do_legend:
        legend_elements = [
            Patch(label="Group A", facecolor=pal[0], edgecolor=pal[0]),
            Patch(label="Group B", facecolor=pal[1], edgecolor=pal[1]),
        ]
        g.ax_marg_x.legend(handles=legend_elements, frameon=False, ncol=2, bbox_to_anchor=(0, 1.4), loc="upper left", fontsize=17)

    # plt.ylim((0, 2))
    if not for_presentation:
        saveimage("{}_2dskilldist_test{}".format(label, teststrlabel), close=False)
    else:
        saveimage("{}_2dskilldist_test{}_presentation".format(label, teststrlabel), close=False, extension="png")

    # sns.set_palette(sns.color_palette("cubehelix", 5))
