# CPAC-QC Plotting App

![CPAC-QC](static/cpac-qc.png)

## Overview

The CPAC-qc Plotting App is a tool designed to generate quality control plots for the CPAC (Configurable Pipeline for the Analysis of Connectomes) outputs. This app helps in visualizing and assessing the quality of neuroimaging data processed through CPAC.

## Features

- Generate bulk or subject specific plots

## Requirements

- Docker or Singularity
- BIDS dir with `.nii.gz` images in it.
- (optional) html preview extension for your editor

## Usage

### Using Docker

1. **Pull the Docker image:**

   ```bash
   docker pull birajstha/cpac-qc:develop
   ```

2. **Run the Docker container:**

   ```bash
   docker run --rm \
       -v /path/to/cpac_output_dir:/cpac_output_dir \
       -v /path/to/qc_dir:/qc_dir \
       birajstha/cpac-qc:develop --n_procs 10
   ```

   Replace `/path/to/cpac_output_dir` and `/path/to/qc_dir` with the actual paths to your CPAC output directory and QC directory, respectively.

### Using Singularity

1. **Build the singularity image from docker:**

   ```bash
   singularity build cpac-qc.sif docker://birajstha/cpac-qc
   ```

2. **Run the Singularity container:**

   ```bash
    singularity run \
        -B $cpac_output_dir:/cpac_output_dir \
        -B $qc_dir:/qc_dir \
        $IMAGE --n_procs 10
   ```

   Replace `/path/to/cpac_output_dir` and `/path/to/qc_dir` with the actual paths to your CPAC output directory and QC directory, respectively.

3. **Run single subject:**

   ```bash
   singularity run \
       -B $cpac_output_dir/$PARTICIPANT:/cpac_output_dir/$PARTICIPANT \
       -B $qc_dir:/qc_dir \
       $IMAGE
   ```

   Replace `/path/to/cpac_output_dir` and `/path/to/qc_dir` with the actual paths to your CPAC output directory and QC directory, respectively.

## Example

Here is an example script to run the CPAC-QC Plotting App:

```bash
#!/bin/bash
#SBATCH --mem=30G
#SBATCH -N 1
#SBATCH -p RM-shared
#SBATCH -t 60:00:00
#SBATCH --ntasks-per-node=20

IMAGE="/ocean/projects/med220004p/bshresth/projects/cpac-qc/cpac-qc.sif"

cpac_output_dir="/ocean/projects/med220004p/bshresth/vannucci/all_runs/scripts/outputs/AFNI_FSL_strict_noBBR_run2/output/pipeline_cpac_fmriprep-options"

qc_dir=/ocean/projects/med220004p/bshresth/projects/images/qc2

singularity run \
    -B $cpac_output_dir:/cpac_output_dir \
    -B $qc_dir:/qc_dir \
    $IMAGE --n_procs 10
```
