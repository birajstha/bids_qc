# CPAC-QC Plotting App

![CPAC-QC](static/cpac-qc.png)

## Overview

The CPAC-qc Plotting App is a tool designed to generate quality control plots for the CPAC (Configurable Pipeline for the Analysis of Connectomes) outputs. This app helps in visualizing and assessing the quality of neuroimaging data processed through CPAC.

## Features

- Generate bulk or subject specific plots

## Requirements

- A html viewing tool or extension
- BIDS dir with `.nii.gz` images in it.

## Installation

```bash
pip install bids_qc
```

## Usage

```bash
bids_qc -d path/to/bids_dir -o path/to/output-qc-dir -n number-of-procs
```
