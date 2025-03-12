from CPACqc.table.utils import gen_resource_name
from CPACqc.table.utils import is_3d_or_4d
from CPACqc.table.utils import fill_space
from CPACqc.logging.log import logger

import os
import pandas as pd

def preprocess(df):
    for col in df.columns:
        if isinstance(df[col].iloc[0], dict):
            df[col] = df[col].apply(lambda x: str(x) if x else "")
            if df[col].nunique() == 1 and df[col].iloc[0] == "":
                df = df.drop(columns=[col])
                
    # give me all columns that have more than one unique value and drop other columns
    # non_single_value_columns = df.columns[df.nunique() > 1].tolist()
    # df = df[non_single_value_columns]

    # fill all columns with NaN with empty string
    df = df.fillna("")

    # drop json column too
    df = df.drop(columns=["json"])

    # give me all whose ext is nii.gz
    nii_gz_files = df[df.file_path.str.endswith(".nii.gz")].copy()

    # add one column that breaks the file_path to the last name of the file and drops extension
    nii_gz_files.loc[:, "file_name"] = nii_gz_files.file_path.apply(lambda x: os.path.basename(x).replace(".nii.gz", ""))

    nii_gz_files.loc[:, "resource_name"] = nii_gz_files.apply(gen_resource_name, axis=1)

    nii_gz_files = nii_gz_files[nii_gz_files.file_path.apply(lambda x: is_3d_or_4d(x))]

    # check if the space column is empty and if empty fill it with T1w if the datatype is anat or with bold if datatype is func, if not empty leave it
    nii_gz_files.loc[:, "space"] = nii_gz_files.apply(lambda x: fill_space(x), axis=1)

    return nii_gz_files