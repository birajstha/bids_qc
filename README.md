[![PyPI Downloads](https://static.pepy.tech/badge/cpacqc)](https://pepy.tech/projects/cpacqc)

# CPAC-QC Plotting App

### PDF Report
example PDF report here: [PDF REPORT](static/sub-PA001_ses-V1W1_qc_report.pdf)

### HTML Report
![CPAC-QC](https://raw.githubusercontent.com/birajstha/bids_qc/main/static/cpac-qc.png)

## Overview

The CPAC-qc Plotting App is a tool designed to generate quality control plots for the CPAC (Configurable Pipeline for the Analysis of Connectomes) outputs. This app helps in visualizing and assessing the quality of neuroimaging data processed through CPAC.

## Updates
- Outputs PDF (default) and HTML report (with -html flag) now.
- [Default config](CPACqc/overlay/overlay.csv) has overlays.

## Features
- Generate bulk or subject specific plots and reports.

## Requirements

- BIDS dir with `.nii.gz` images in it.
- (Optional) A html viewing tool or extension
- PDF viewer

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
cpacqc -d bids_dir -s subject-id_1 subject-id_2
```

You can hand pick a single or a multiple subjects with `-s` flag


4. **Running with defined number of procs**

```bash
cpacqc -d path/to/bids_dir  -n number-of-procs
```

Note: if -n is not provided default is 8


5. **Running all Subjects in the dir**

```bash
cpacqc -d path/to/bids_dir 
```

or simply

```bash
cpacqc -d path/to/bids_dir
```


6. **Providing Overlays config**

```bash
cpacqc -d path/to/bids_dir -c ./overlay.csv
```

where overlay.csv can be in format

```csv
output,underlay
desc-preproc_bold, desc-preproc_T1w
```

and so on.
If not provided a [default config](CPACqc/overlay/overlay.csv) will be used.

## Viewing

Use any PDF viewer to view `*report.pdf` file.

If `-html` enabled, Use any `.html` viewer extension to view `index.html` in the `results` dir.
