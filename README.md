[![PyPI Downloads](https://static.pepy.tech/badge/cpacqc)](https://pepy.tech/projects/cpacqc)

# CPAC-QC Plotting App

### PDF Report
![PDF report](https://raw.githubusercontent.com/birajstha/bids_qc/main/static/cpac-qc_pdf.png)
example PDF report here: [PDF REPORT](https://github.com/birajstha/bids_qc/raw/main/static/sub-PA001_ses-V1W1_qc_report.pdf)


## Overview

The CPAC-qc Plotting App is a tool designed to generate quality control plots for the CPAC (Configurable Pipeline for the Analysis of Connectomes) outputs. This app helps in visualizing and assessing the quality of neuroimaging data processed through CPAC.

## Updates
- Outputs only PDF report now.
- [Default config](https://github.com/birajstha/bids_qc/raw/main/CPACqc/overlay/overlay.csv) has overlays.
- Images on PDF report will follow the order mentioned in overlay.csv provided or default.
- Added Bookmarks on PDF report for easy navigation.

## Features
- Generate bulk or subject specific plots and reports.

## Requirements

- BIDS dir with `.nii.gz` images in it.
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

2. **Providing output dir**

```bash
cpacqc -d bids_dir -o output_dir
```
output_dir will be created if not available. Make sure to have write permissions.

3. **Running single/multiple Subjects**

```bash
cpacqc -d bids_dir -s subject-id_1 subject-id_2
```

You can hand pick a single or a multiple subjects with `-s` flag


4. **With defined number of procs**

```bash
cpacqc -d bids_dir  -n number-of-procs
```

Note: if -n is not provided default is 8


5. **Providing custom Overlays config**

```bash
cpacqc -d path/to/bids_dir -c ./overlay.csv
```

where overlay.csv can be in format

```csv
output,underlay,datatype
desc-preproc_bold,desc-preproc_T1w,func
```

and so on.
If not provided a [default config](https://github.com/birajstha/bids_qc/raw/main/CPACqc/overlay/overlay.csv) will be used.

## Viewing

Use any PDF viewer to view `*report.pdf` file.

If `-html` enabled, Use any `.html` viewer extension to view `index.html` in the `results` dir.