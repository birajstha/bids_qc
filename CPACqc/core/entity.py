
from dataclasses import dataclass, field
from typing import Optional
import os
import pandas
from CPACqc.utils.logging.log import FileLogger as logger
from CPACqc.core.utils import *
import json


@dataclass
class Table:
    
    original_table:Optional[pandas.DataFrame]
    processed_table:Optional[pandas.DataFrame] = field(init=False)
    all_columns_old = ['dataset', 'dataset_type', 'dataset_path', 'dataset_description', 'sub',
       'ses', 'datatype', 'suffix', 'ext', 'extra_entities', 'sample', 'task',
       'tracksys', 'acq', 'nuc', 'voi', 'ce', 'trc', 'stain', 'rec', 'dir',
       'run', 'mod', 'echo', 'flip', 'inv', 'mt', 'part', 'proc', 'hemi',
       'space', 'split', 'recording', 'chunk', 'seg', 'res', 'den', 'label',
       'desc', 'json', 'file_path', 'link_target', 'mod_time', 'file_name',
       'resource_name', 'sub_ses', 'scan']
    all_columns_new = ['dataset', 'sub', 'ses', 'sample', 'task', 'tracksys', 'acq', 'nuc',
       'voi', 'ce', 'trc', 'stain', 'rec', 'dir', 'run', 'mod', 'echo', 'flip',
       'inv', 'mt', 'part', 'proc', 'hemi', 'space', 'split', 'recording',
       'chunk', 'seg', 'res', 'den', 'label', 'desc', 'datatype', 'suffix',
       'ext', 'extra_entities', 'root', 'path']

    columns_to_keep = ['sub', 'ses', 'file_path', 'file_name', 'resource_name', 'datatype', 'space', 'scan', 'json']

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
        print(Fore.YELLOW + "Preprocessing the original table..." + Fore.RESET)
        df = self.original_table
        # Convert all dicts/lists in every column to string
        for col in df.columns:
            df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
        df = df.fillna("")  # <-- Fill NAs before any comparison

        # Now safe to check for empty columns
        for col in df.columns:
            if df[col].nunique() == 1 and df[col].iloc[0] == "":
                df = df.drop(columns=[col])

        df = df.astype(str)

        files = ["nii.gz", ".nii"]

        # Filter rows where file_path ends with .nii.gz or .nii
        nii_gz_files = df[df.path.str.endswith(tuple(files))]

        # Filter rows and omit xfm.nii.gz files
        nii_gz_files = nii_gz_files.loc[~nii_gz_files.path.str.contains("xfm.nii.gz")]

        # Add a column that breaks the file_path to the last name of the file and drops extension
        nii_gz_files.loc[:, "file_name"] = nii_gz_files.path.apply(lambda x: os.path.basename(x).split(".")[0])
        # Combine sub and ses columns to create a new column called sub_ses
        nii_gz_files.loc[:, "sub_ses"] = nii_gz_files.apply(get_sub_ses, axis=1)
        nii_gz_files.loc[:, "resource_name"] = nii_gz_files.apply(lambda row: gen_resource_name(row), axis=1)

        # add root column and path column to save as file_path
        nii_gz_files.loc[:, "file_path"] = nii_gz_files.apply(lambda row: os.path.join(row.root, row.path), axis=1)
        nii_gz_files.loc[:, "json_path"] = nii_gz_files.apply(lambda row: os.path.join(row.root, row.path.replace(".nii.gz", ".json")), axis=1)
        nii_gz_files.loc[:, "json"] = nii_gz_files["json_path"].apply(safe_load_json)

        nii_gz_files = nii_gz_files[nii_gz_files.file_path.apply(lambda x: is_3d_or_4d(x))]

        # Check if the space column is empty and fill it accordingly
        nii_gz_files.loc[:, "space"] = nii_gz_files.apply(lambda x: fill_space(x), axis=1)

        # Create a new column called scan that combines task and run columns
        nii_gz_files.loc[:, "scan"] = nii_gz_files.apply(get_scan, axis=1)

        nii_gz_files.loc[:, "datatype"] = nii_gz_files.apply(lambda x: get_datatype(x), axis=1)

        self.processed_table = nii_gz_files

def get_datatype(row):
    datatype = (
        row["path"]
        .replace(".nii.gz", "")
        .replace(".nii", "")
        .replace(row["resource_name"], "")
        .replace(f"sub-{row['sub']}", "")
        .replace(f"ses-{row['ses']}", "")
        .replace(f"space-{row['space']}", "")
        .replace(row["scan"], "")
        .replace("_", "")
        .replace("-", "")
        .replace("/", "")
    )
    return datatype


    

def safe_load_json(json_path):
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                json_metadata = clean_and_flatten_json_column(json.load(f))
                return json_metadata
        except Exception as e:
            logger.error(f"Could not load JSON: {json_path} ({e})")
            return None
    else:
        return None

@dataclass
class Resource:
    """
    Class to represent a resource in the table.
    """
    sub: str
    ses: str
    file_path: str
    file_name: str
    resource_name: str
    datatype: str
    space: str
    scan: str
    json: Optional[str] = None

    
    