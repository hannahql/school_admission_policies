from visualization.fancier_plots import *
import copy


def plot_2d_IF(dff, label, equivariance=None, xvarlabel="FEATURE_DIST_B1_var", IFcol="IF", true_skill_range=None):
    varlabel = axis_label_map.get(xvarlabel, xvarlabel)
    xlabel = "True skill $q$"

    if IFcol == "IF":
        ymin = 0.5
        ymax = 1
    else:
        ymin = 0.00001
        ymax = 3

    dffIF = copy.copy(dff.dropna(subset=[IFcol]).query("label==@label"))
    dffIF.loc[:, IFcol] = dffIF[IFcol].apply(eval)
    dffIF.loc[:, "IFpair"] = dffIF[IFcol].apply(lambda x: [(y, x[y]) for y in x])
    dffIF = dffIF.explode("IFpair")
    dffIF[[xlabel, IFcol]] = pd.DataFrame([*dffIF.IFpair], dffIF.index)
    dffIF.loc[:, xlabel] = pd.to_numeric(dffIF[xlabel])
    if true_skill_range is not None:
        ymin, ymax = true_skill_range
        if dffIF[xlabel].max() <= 1.000001 and ymax > 1:
            dffIF.loc[:, xlabel] = ymin + dffIF[xlabel] * (ymax - ymin)
    dffIF[[xlabel]] = dffIF[[xlabel]]  # .round(4)
    dffIF[[varlabel]] = dffIF[[xvarlabel]]  # .round(1)
    dffIF = dffIF.groupby([xlabel, varlabel])[IFcol].agg(np.nanmean).reset_index()
    dffIF = dffIF.loc[(dffIF[xlabel] >= ymin) & (dffIF[xlabel] <= ymax), :].reset_index()
    dffIF.loc[:, "IF"] = dffIF[IFcol]
    pivot = dffIF.pivot(index=xlabel, columns=varlabel, values="IF")
    if true_skill_range is not None:
        target_index = np.linspace(ymin, ymax, 201)
        pivot = (
            pivot.reindex(pivot.index.union(target_index))
            .sort_index()
            .interpolate(method="index")
            .reindex(target_index)
        )
    if equivariance is not None:
        equivarianceloc = (dffIF[varlabel] - equivariance).abs().idxmin()
    from matplotlib.ticker import FixedFormatter

    ax = sns.heatmap(pivot, cmap=sns.color_palette("vlag", as_cmap=True), xticklabels=5, yticklabels=40, vmin=-1, vmax=1)
    ax.invert_yaxis()

    xticks = ax.get_xticks()
    yticks = ax.get_yticks()
    ax.set_xticks(xticks)
    ax.set_yticks(yticks)
    ax.set_xticklabels([format_heatmap_ticklabel(label.get_text(), 1) for label in ax.get_xticklabels()])
    ax.set_yticklabels([format_heatmap_ticklabel(label.get_text(), 1) for label in ax.get_yticklabels()])

    plt.ylabel(xlabel, size=20)
    plt.xlabel(varlabel, size=20)

    if equivariance is not None:
        ax.vlines(x=equivarianceloc, ymin=0, ymax=dffIF.shape[0], linewidth=2)
        ax.text(equivarianceloc + 0.5, 15, "Equal precision", ha="left", va="center", fontsize=17)
    saveimage("{}_2dIF_{}".format(label, xvarlabel), close=False)


def plot_individual_fairness_curves_clean(
    dff,
    label,
    school_names=school_names_pretty,
    # schools_todo=schoolorder_default,
    schoolorder=schoolorder_default,
    grouprename=group_names_pretty,
    do_percentile=False,
    IFcol="IF",
    num_x_bins=20,
    savenameappend="",
    legend_offset=1.1,
):
    xlabel = "True skill $q$"
    if IFcol == "IF":
        ymin = 0.5
        ymax = 1
    else:
        ymin = 0.00001
        ymax = 3
    dffIF = copy.copy(dff.dropna(subset=[IFcol]).query("label==@label"))
    dffIF.loc[:, IFcol] = dffIF[IFcol].apply(eval)
    dffIF.loc[:, "IFpair"] = dffIF[IFcol].apply(lambda x: [(y, x[y]) for y in x])

    dffIF = dffIF.explode("IFpair")
    dffIF[[xlabel, IFcol]] = pd.DataFrame([*dffIF.IFpair], dffIF.index)
    # dffIF = dffIF.groupby([xlabel, "school_type"])[IFcol].agg(np.nanmean).reset_index()
    dffIF = dffIF.loc[(dffIF[xlabel] >= ymin) & (dffIF[xlabel] <= ymax), :].reset_index()
    dffIF.loc[:, "IF"] = dffIF[IFcol]

    roundmult = (dffIF[xlabel].max() - dffIF[xlabel].min()) / (num_x_bins / 10)
    dffIF[xlabel] = (dffIF[xlabel] / roundmult).round(1) * roundmult
    print(dffIF[xlabel].nunique())

    dffIF.loc[:, "Estimation and selection policy"] = dffIF.school_type.replace(school_names)
    dffIF.loc[:, "Testing Policy"] = dffIF["Estimation and selection policy"].apply(
        lambda x: "Test-based" if "test-based" in x else "Test-free"
    )
    dffIF.loc[:, "Estimation and selection policy"] = dffIF["Estimation and selection policy"].str.replace(", test-based", "")
    dffIF.loc[:, "Estimation and selection policy"] = dffIF["Estimation and selection policy"].str.replace(", test-free", "")

    print(dffIF["Estimation and selection policy"].unique())

    sns.set_palette(sns.color_palette("cubehelix", len(schoolorder)))

    sns.lineplot(
        x=xlabel,
        y="IF",
        hue="Estimation and selection policy",
        style="Testing Policy",
        style_order=["Test-based", "Test-free"],
        hue_order=schoolorder,
        data=dffIF,
        linewidth=2,
    )
    plt.xlim((ymin, ymax))
    plt.legend(frameon=False, bbox_to_anchor=(-0.025, legend_offset), loc="upper left")
    # plt.legend(frameon=False, bbox_to_anchor=(-0.025, 1.25), loc="upper left")

    plt.xlabel(xlabel, fontsize=20)
    plt.ylabel("Individual Fairness gap", fontsize=20)
    saveimage("{}_{}{}".format(label, "indivfairness", savenameappend), close=False)
    sns.set_palette(sns.color_palette("cubehelix", 5))

    return dffIF


def plot_individual_fairness_curves(
    dff,
    label,
    school_names=school_names_pretty,
    schools_todo=schoolorder_default,
    schoolorder=schoolorder_default,
    grouprename=group_names_pretty,
    roundmult=2,
    do_percentile=False,
):
    dfloc = dff.query('(label == "{}")'.format(label))
    toconcat = []

    for ennn, hashh in enumerate(dfloc.hash.unique()):
        df = dfloc.query("hash == @hashh")
        students_df = pd.read_csv("generated_data/{}__{}.csv".format(label, hashh))
        # print(hashh)
        for en, school in df.iterrows():
            admitlist = eval_list(school.admitted_students)
            rejectlist = list(set(students_df.index) - set(admitlist))
            admits = students_df.iloc[admitlist]
            admits.loc[:, "admitted"] = True
            rejects = students_df.iloc[rejectlist]
            rejects.loc[:, "admitted"] = False
            admits.loc[:, "school_type"] = school.school_type
            rejects.loc[:, "school_type"] = school.school_type
            toconcat.extend([admits, rejects])
    dfstudentadmits = pd.concat(toconcat)
    # print(dfstudentadmits.shape)

    if do_percentile:
        dfstudentadmits.loc[:, "skillcut"] = (dfstudentadmits.skill.rank(pct=True) * roundmult).round(1) / roundmult
    else:
        roundmultskill = int(np.ceil(roundmult / (dfstudentadmits.skill.max() - dfstudentadmits.skill.min()) * 2))
        dfstudentadmits.loc[:, "skillcut"] = (dfstudentadmits.skill * roundmultskill).round(1) / roundmultskill

    # dfstudentadmits.loc[:, "Group"] = dfstudentadmits["group"]  # .replace(grouprename)
    dfstudentadmits = dfstudentadmits[dfstudentadmits.school_type.isin(schools_todo)]
    # schoolordernames = [school_names[x] for x in schoolorder]
    # dfstudentadmits.loc[:, "School Policy"] = dfstudentadmits["school_type"].replace(school_names)
    # dfstudentadmits.loc[:, "Skill"] = dfstudentadmits["skillcut"]
    # dfstudentadmits.loc[:, "Pr(Admission)"] = dfstudentadmits["admitted"]
    dftoplot = dfstudentadmits.groupby(["school_type", "skillcut", "group"])["admitted"].mean().reset_index()
    # dftoplot = dfstudentadmits
    # print(dftoplot.head())
    concats = []
    for school in dfstudentadmits.school_type.unique():
        # print(school)
        for skill in dfstudentadmits.skillcut.unique():
            quera = dftoplot.query('school_type==@school and skillcut==@skill and group=="A"')
            querb = dftoplot.query('school_type==@school and skillcut==@skill and group=="B"')
            if quera.shape[0] < 1 or querb.shape[0] < 1:
                # print(school, skill)
                continue
            groupaprob = quera.iloc[0]["admitted"].astype(float)
            groupbprob = querb.iloc[0]["admitted"].astype(float)
            concats.append(
                {"Estimation and selection policy": school, "Skill": skill, "Difference in individual fairness": groupaprob - groupbprob}
            )
    dftoplot = pd.DataFrame(concats)
    # school_names_loc = {"{}: {}".format(school_names_notation[x], school_names[x]) for x in school_names}
    dftoplot.loc[:, "Estimation and selection policy"] = dftoplot["Estimation and selection policy"].replace(school_names)
    # print(dftoplot.head())
    # dftoplot.loc[:, "Affirmative Action"] = dftoplot["Estimation and selection policy"].apply(lambda x: "with affirmative action" in x)
    dftoplot.loc[:, "Testing Policy"] = dftoplot["Estimation and selection policy"].apply(
        lambda x: "Test-based" if "test-based" in x else "Test-free"
    )
    dftoplot.loc[:, "Estimation and selection policy"] = dftoplot["Estimation and selection policy"].str.replace(", test-based", "")
    dftoplot.loc[:, "Estimation and selection policy"] = dftoplot["Estimation and selection policy"].str.replace(", test-free", "")
    sns.set_palette(sns.color_palette("cubehelix", len(dftoplot["Estimation and selection policy"].unique())))
    # print(dftoplot["Testing Policy"].unique())
    # print(dftoplot["Estimation and selection policy"].unique())
    # print(schoolorder)

    sns.lineplot(
        x="Skill $q$",
        y="Difference in individual fairness",
        hue="Estimation and selection policy",
        style="Testing Policy",
        style_order=["Test-based", "Test-free"],
        hue_order=schoolorder,
        data=dftoplot,
        linewidth=3,
    )
    plt.xlim((-1, 4))
    # plt.legend(frameon=False, bbox_to_anchor=(-0.15, -0.05), loc="upper left")
    plt.legend(frameon=False, bbox_to_anchor=(-0.025, 1.4), loc="upper left")

    plt.xlabel("Skill", fontsize=20)
    plt.ylabel("Individual Fairness gap", fontsize=20)
    # dfstudentadmits.loc[:, "skillcut"] = (dfstudentadmits.skill.rank(pct=True) * 2).round(1) / 2
    # # dftoplot = dfstudentadmits.groupby(["school_type", "skillcut"])["admitted"].mean().reset_index()
    # dfstudentadmits.loc[:, "Group"] = dfstudentadmits["group"].replace(grouprename)
    # dfstudentadmits = dfstudentadmits[dfstudentadmits.school_type.isin(schoolorder)]
    # schoolordernames = [school_names[x] for x in schoolorder]
    # dfstudentadmits.loc[:, "School Policy"] = dfstudentadmits["school_type"].replace(school_names)
    # dfstudentadmits.loc[:, "Skill"] = dfstudentadmits["skillcut"]
    # dfstudentadmits.loc[:, "Pr(Admission)"] = dfstudentadmits["admitted"]
    # dftoplot = dfstudentadmits.groupby(["School Policy", "Skill", "Group"])["Pr(Admission)"].mean().reset_index()
    # sns.set_palette(sns.color_palette("cubehelix", len(schoolordernames)))
    # sns.lineplot(x="Skill", y="Pr(Admission)", hue="School Policy", style="Group", hue_order=schoolordernames, data=dftoplot, linewidth=3)
    # plt.xlim((0.2, 1))
    # plt.legend(frameon=False, bbox_to_anchor=(1.0, 1.0), loc="upper left")
    # plt.xlabel("Skill", fontsize=20)
    # plt.ylabel("Pr(Admission)", fontsize=20)
    saveimage("{}_{}".format(label, "indivfairness"), close=False)
    sns.set_palette(sns.color_palette("cubehelix", 5))

    return dftoplot
