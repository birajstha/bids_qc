
from dataclasses import dataclass, field
from typing import Optional
import os
import pandas
from CPACqc.utils.logging.log import FileLogger as logger
from CPACqc.core.utils import *

@dataclass
class Table:
    
    original_table:Optional[pandas.DataFrame]
    processed_table:Optional[pandas.DataFrame] = field(init=False)
    
    def __post_init__(self):
        """
        Initialize the Table class and preprocess the original table.
        """
        if self.original_table is None:
            raise ValueError("original_table cannot be None")
        
        # Check if the original table is empty
        if self.original_table.empty:
            logger.error("The original table is empty.")
            raise ValueError("The original table is empty.")
        
        # Preprocess the original table
        self.preprocess()

        
    def preprocess(self):
        """
        Preprocess the original table to extract relevant information.
        """
        df = self.original_table.copy()
        for col in df.columns:
            if isinstance(df[col].iloc[0], dict):
                df[col] = df[col].apply(lambda x: str(x) if x else "")
                if df[col].nunique() == 1 and df[col].iloc[0] == "":
                    df = df.drop(columns=[col])
        
        # Fill all columns with NaN with empty string
        df = df.fillna("")

        files = ["nii.gz", ".nii"]

        # Filter rows where file_path ends with .nii.gz or .nii
        nii_gz_files = df[df.file_path.str.endswith(tuple(files))]

        # Filter rows and omit xfm.nii.gz files
        nii_gz_files = nii_gz_files.loc[~nii_gz_files.file_path.str.contains("xfm.nii.gz")]

        # Add a column that breaks the file_path to the last name of the file and drops extension
        nii_gz_files.loc[:, "file_name"] = nii_gz_files.file_path.apply(lambda x: os.path.basename(x).split(".")[0])
        
        nii_gz_files.loc[:, "resource_name"] = nii_gz_files.apply(lambda row: gen_resource_name(row), axis=1)

        nii_gz_files = nii_gz_files[nii_gz_files.file_path.apply(lambda x: is_3d_or_4d(x))]

        # Check if the space column is empty and fill it accordingly
        nii_gz_files.loc[:, "space"] = nii_gz_files.apply(lambda x: fill_space(x), axis=1)

        # Combine sub and ses columns to create a new column called sub_ses
        nii_gz_files.loc[:, "sub_ses"] = nii_gz_files.apply(get_sub_ses, axis=1)

        # Create a new column called scan that combines task and run columns
        nii_gz_files.loc[:, "scan"] = nii_gz_files.apply(get_scan, axis=1)

        self.processed_table = nii_gz_files

