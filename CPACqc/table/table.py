from CPACqc.table.utils import *
from CPACqc.logging.log import logger

import os
import pandas as pd

def preprocess(df):
    for col in df.columns:
        if isinstance(df[col].iloc[0], dict):
            df[col] = df[col].apply(lambda x: str(x) if x else "")
            if df[col].nunique() == 1 and df[col].iloc[0] == "":
                df = df.drop(columns=[col])
    

    # Fill all columns with NaN with empty string
    df = df.fillna("")

    # Drop json column if it exists
    if "json" in df.columns:
        df = df.drop(columns=["json"])

    # Filter rows where file_path ends with .nii.gz
    nii_gz_files = df[df.file_path.str.endswith(".nii.gz")].copy()

    # Add a column that breaks the file_path to the last name of the file and drops extension
    nii_gz_files.loc[:, "file_name"] = nii_gz_files.file_path.apply(lambda x: os.path.basename(x).replace(".nii.gz", ""))

    nii_gz_files.loc[:, "resource_name"] = nii_gz_files.apply(gen_resource_name, axis=1)

    nii_gz_files = nii_gz_files[nii_gz_files.file_path.apply(lambda x: is_3d_or_4d(x))]

    # Check if the space column is empty and fill it accordingly
    nii_gz_files.loc[:, "space"] = nii_gz_files.apply(lambda x: fill_space(x), axis=1)

    # Combine sub and ses columns to create a new column called sub_ses
    nii_gz_files.loc[:, "sub_ses"] = nii_gz_files.apply(get_sub_ses, axis=1)

    # Create a new column called scan that combines task and run columns
    nii_gz_files.loc[:, "scan"] = nii_gz_files.apply(get_scan, axis=1)

    return nii_gz_files