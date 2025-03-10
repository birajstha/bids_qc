[![PyPI Downloads](https://static.pepy.tech/badge/cpacqc)](https://pepy.tech/projects/cpacqc)

# CPAC-QC Plotting App

![CPAC-QC](https://raw.githubusercontent.com/birajstha/bids_qc/main/static/cpac-qc.png)

## Overview

The CPAC-qc Plotting App is a tool designed to generate quality control plots for the CPAC (Configurable Pipeline for the Analysis of Connectomes) outputs. This app helps in visualizing and assessing the quality of neuroimaging data processed through CPAC.

## Features

- Generate bulk or subject specific plots
- Outputs PDF (default) and HTML report (with -html flag)

## Requirements

- BIDS dir with `.nii.gz` images in it.
- (Optional) A html viewing tool or extension

## Installation

```bash
pip install CPACqc
```

## Usage


1. **Minimal code**

```bash
cpacqc -d bids_dir
```

This will output a pdf report `report.pdf` in your current directory.


2. **HTML report**

```bash
cpacqc -d bids_dir -html
```

This will create a pdf `report.pdf` along with a `results` dir with HTML report `index.html` and related files.


3. **Running single/multiple Subjects**

```bash
cpacqc -d path/to/bids_dir -o path/to/output-qc-dir -s subject-id_1 subject-id_2
```

You can hand pick a singl or a few subjects with `-s` flag


4. **Running Single Subject with defined number of procs**

```bash
cpacqc -d path/to/bids_dir -o path/to/output-qc-dir -s subject-id -n number-of-procs
```

Note: if -n is not provided default is 8


5. **Running all Subjects in the dir**

```bash
cpacqc -d path/to/bids_dir -o path/to/output-qc-dir
```

or simply

```bash
cpacqc -d path/to/bids_dir
```


6. **Plotting Overlays**

```bash
cpacqc -d path/to/bids_dir -o qc_dir -c ./overlay.csv
```

where overlay.csv can be in format

```csv
image_1,image_2
desc-preproc_bold, desc-preproc_T1w
```

and so on.


## Viewing

Use any .html viewer extension to view index.html
