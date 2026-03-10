# School Admission Policies 

This repository implements simulations for the paper [Dropping Standardized Testing for Admissions Trades Off Information and Access](https://arxiv.org/abs/2010.04396).

## Overview

This codebase implements a simulation framework for studying school admission policies and their effects on different student populations. It supports various scenarios including:
- Single school admissions
- Multiple school admissions with market dynamics
- Analysis of admission barriers (e.g., test-taking) under settings where students are strategic and non-strategic

## Project Structure

```
.
├── data/                   # Data directory for input datasets
├── simulations/           # Core simulation code
├── generic/               # Utility functions and helpers
└── README.md             # This file
```

## Data Requirements

**Note:** The THEOP dataset is not included in this repository. Access requires submitting an application directly to the THEOP project. The processed data is maintained in a separate private repository. If you are a reviewer or collaborator and need access, please contact the authors.

To run the simulations using real data, you will need to obtain the Texas Higher Education Opportunity Project (THEOP) dataset. Follow these steps:

1. Apply for access and obtain the data from the THEOP website [https://theop.princeton.edu/](https://theop.princeton.edu/)
2. Once you have the data, create a `data/theop/` directory in the project root and organize the THEOP files as follows:

The code expects STATA data files (.dta) for each university's applications and transcripts in this format:
```
data/theop/
├── theop_au_applications.dta    # UT Austin applications
├── theop_au_transcripts.dta     # UT Austin transcripts
├── theop_amk_applications.dta   # Texas A&M Kingsville applications
├── theop_amk_transcripts.dta    # Texas A&M Kingsville transcripts
└── [similar files for other universities]
```

The dataset also includes files for the following universities (institution codes):
- Texas A&M (am)
- Texas A&M Kingsville (amk)
- UT Arlington (ar)
- UT Austin (au)
- UT Pan American (pa)
- Texas Tech (tt)
- Rice (ri)
- Southern Methodist University (sm)

See [Expected Data Format](#expected-data-format) at the end of this document for the required column specifications.


## Configuration Parameters

The simulation framework is configurable through various parameters:

### Student Parameters
- `NUM_STUDENTS`: Total number of students in simulation
- `NUM_GROUPS`: Number of demographic groups
- `FRACTIONS_GROUPS`: Distribution of students across groups

### Simulation Types

1. SINGLE_SCHOOL
   - Basic single school admission simulation
   - Configurable admission functions and skill estimation methods
   - Nonstrategic student test access

2. MARKET
   - Multiple schools competing for students, schools have different rankings
  - Student order of school preferences is randomized
  - Number of each school type is determined by `NUM_SCHOOLS * FRACTION_OF_SCHOOL_TYPES`
  - Nonstrategic student test access

3. MARKET_FIX_SCHOOL_ATTRIBUTES
   - Multiple schools competing for students, schools have different rankings
   - Allows explicit specification of: School rankings and atatributes
   - Nonstrategic student test access

4. SINGLE_SCHOOL_COST_MODEL
   - Extends single school model to incorporate students' strategic test taking behavior
   - Student observes their other $K-1$ features and decides whether to take the test, based on expected utility
   - Supports group-specific test costs 



5. TWO_SCHOOL_COST_MODEL
   - Two school model with strategic student behavior
   - Incorporates school quality (utilities) affecting student preferences
   - Spillover effects of one school's admission policy on the pool of students who apply to another school

## Basic Usage

1. Configure simulation parameters in `simulations/settings.py`
2. Run simulations using the pipeline:

```python
from pipeline import pipeline

# Define custom parameters
parameters = {
    "SIMULATION_TYPE": "SINGLE_SCHOOL",
    "NUM_STUDENTS": 1000,
    "NUM_GROUPS": 2,
    "FRACTIONS_GROUPS": [0.5, 0.5]
}

# Run simulation
students_df, schools_df, params = pipeline(parameters)
```

## Paper Replication

This repository includes three notebooks that reproduce the key results from our paper:

1. `pipeline_use_paperfigures_single_school_strategic.ipynb`: Contains code to recreate figures for single school strategic plots, including:
   - Visualization of student test taking behavior, as a function of true skill
   - Visualization of admission metrics at different cost levels

2. `pipeline_use_paperfigures_two_school_strategic.ipynb`: Reproduces the two-school strategic model figures, including:
   - Payoff matrix heatmaps showing average admitted skill for both schools
   - All four policy combinations (both schools use test, both drop test, or one of each)
   - Spillover effects of one school's test policy on the other school's admitted class
   - **Note:** This notebook loads pre-computed simulation results from disk. Before running it, you must first run `run_two_school_cost_model.py` to generate the simulation data.

3. `pipeline_use_calibrated_data_2025.ipynb`: Reproduces the calibrated simulations using THEOP data from 1992-1997. This notebook:
   - Calibrates model parameters using data from THEOP, under hypothetical honors program described in paper
   - Simulates admission outcomes under different policy scenarios
   - Compares admission metrics from different policies
   - Compares admission metrics across two hypothetical informational regimes (low and high)



---

## Expected Data Format

**Application files** (`theop_{code}_college_applications.dta`) must contain the following columns:

| Column | Description |
|--------|-------------|
| `studentid` | Student identifier |
| `yeardes` / `termdes` | Application year and term |
| `male` | Gender indicator |
| `ethnic` | Ethnicity |
| `decileR` | High school class rank decile (e.g., "Top 10%", "Second Decile", ...) — mapped to numeric values 0.3–0.9 |
| `hseconstatus` | Socioeconomic status quartile (e.g., "Upper quartile") — mapped to 0, 0.25, 0.5, 0.75 |
| `testscoreR` | Test score as a string range (e.g., "1200-1400") — midpoint is extracted |
| `major_field` | Intended major field |
| `hsprivate` / `hstypeR` / `hsinstate` | High school characteristics |
| `admit` / `enroll` | Admission and enrollment outcomes |
| `gradyear` | Graduation year |

**Transcript files** (`theop_{code}_college_transcripts.dta`) must contain:

| Column | Description |
|--------|-------------|
| `studentid` | Student identifier (joined to applications) |
| `hrearn` | Credit hours earned per term (string range, midpoint extracted) |
| `semgpa` | Semester GPA (string range, midpoint extracted) |
| `cgpa` | Cumulative GPA |
| `year` / `term` | Academic period |
| `term_major_dept` / `term_major_field` | Major department and field per term |

The code computes two GPA measures from transcripts: **first-year GPA** (after 24+ credit hours) and **overall GPA** (all subsequent semesters).
