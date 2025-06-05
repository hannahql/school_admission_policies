import copy
import uuid

from generic.latexify import *
from generic.pandas_apply_parallel import *
import multiprocessing

from pipeline import pipeline
from save_results import save_results_multiple, param_file_global, schoolsdf_file_global

from datetime import datetime


def param_generator_single(fixed_parameters, vary_parameter, vary_parameter_values, repeat_params=5):
    fixlocal = copy.deepcopy(fixed_parameters)
    for _ in range(repeat_params):
        for v in vary_parameter_values:
            fixlocal[vary_parameter] = v
            yield fixlocal


def param_generator_double(
    fixed_parameters, vary_parameter, vary_parameter_values, vary_parameter2, vary_parameter_values2, repeat_params=5
):
    fixlocal = copy.deepcopy(fixed_parameters)
    for _ in range(repeat_params):
        for v in vary_parameter_values:
            for v2 in vary_parameter_values2:
                fixlocal[vary_parameter] = v
                fixlocal[vary_parameter2] = v2
                yield fixlocal


def param_generator_double_variancetogether(
    fixed_parameters, vary_parameter_array, vary_parameter_values, vary_parameter2, vary_parameter_values2, repeat_params=5
):
    fixlocal = copy.deepcopy(fixed_parameters)
    for _ in range(repeat_params):
        for v in vary_parameter_values:
            for v2 in vary_parameter_values2:
                for vp in vary_parameter_array:
                    fixlocal[vp] = v
                fixlocal[vary_parameter2] = v2
                yield fixlocal


def param_generator_nonevary(parameters, repeat_params=5):
    for _ in range(repeat_params):
        yield copy.deepcopy(parameters)


def pipeline_run_parallel(
    param_generator,
    runlabel="",
    num_processes=4,
    param_file=param_file_global,
    schoolsdf_file=schoolsdf_file_global,
    parallel=True,
):
    if parallel:
        pool = multiprocessing.Pool(num_processes)
    count = 0

    runhashstosave = []
    students_dftosave = []
    schools_dftosave = []
    params_tosave = []
    paramdf = None
    metricdf = None

    def in_loop(x):
        nonlocal runhashstosave, students_dftosave, schools_dftosave, params_tosave, count, paramdf, metricdf
        students_df, schools_df, params = x
        runhash = datetime.now().strftime("%Y%m%d_%H%M_{}".format(uuid.uuid4().hex[0:7]))

        runhashstosave.append(runhash)
        students_dftosave.append(students_df)
        schools_dftosave.append(schools_df)
        params_tosave.append(params)

        if count % 20 == 0:
            print(runlabel, runhash[count % 20], count)
            paramdf, metricdf = save_results_multiple(
                runlabel,
                runhashstosave,
                students_dftosave,
                schools_dftosave,
                params_tosave,
                param_file=param_file,
                schoolsdf_file=schoolsdf_file,
                current_param_df=paramdf,
                current_metric_df=metricdf,
            )
            runhashstosave = []
            students_dftosave = []
            schools_dftosave = []
            params_tosave = []
        count += 1

    if parallel:
        for x in pool.imap_unordered(pipeline, param_generator):
            in_loop(x)
    else:
        for param in param_generator:
            x = pipeline(param)
            in_loop(x)

    print(runlabel, count)
    save_results_multiple(
        runlabel,
        runhashstosave,
        students_dftosave,
        schools_dftosave,
        params_tosave,
        param_file=param_file,
        schoolsdf_file=schoolsdf_file,
        current_param_df=paramdf,
        current_metric_df=metricdf,
    )
