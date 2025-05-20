import pandas as pd
import os
import argparse
from multiprocessing import Pool
from tqdm import tqdm
from functools import lru_cache
import tempfile
import bids2table as b2t

import nibabel as nib
from nibabel.orientations import io_orientation, ornt2axcodes
from colorama import Fore, Style, init

import json
import re
from fnmatch import fnmatch

import ast
from CPACqc.core.logger import logger


def make_dir(path) -> None: 
    """
    Create a directory if it doesn't exist.
    
    Parameters:
    path (str): The path to the directory to create.

    Returns:
    pathlib.Path: The created or existing directory.
    """
    path = pathlib.Path(path)
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        message = f"Error creating directory {path}: {e}"
        logger.error(message=message)
        return None


def get_file_info(file_path):
    try:
        img = nib.load(file_path)
        resolution = tuple(float(x) for x in img.header.get_zooms())
        dimension = tuple(int(x) for x in img.shape)
        
        affine = img.affine
        orientation = "".join(ornt2axcodes(io_orientation(affine))) + " @nibabel"
        
        if len(dimension) == 4:
            # get TR info
            tr = float(img.header.get_zooms()[3])
            nos_tr = str(int(img.shape[-1]))
        else:
            tr = None
            nos_tr = None

        return json.dumps({
            "resolution": resolution,
            "dimension": dimension,
            "tr": tr,
            "nos_tr": nos_tr,
            "orientation": orientation
        })
    except Exception as e:
        message = f"Error processing file {file_path}: {e}"
        logger.error(message=message)
        return None

def gen_resource_name(row):
    sub_ses = row["sub_ses"]

    # Handle task, run, acq flexibly
    task = row.get("task", "") or ""
    run = row.get("run", "") or ""
    acq = row.get("acq", "") or ""

    # Build scan pattern based on available fields
    scan_parts = []
    if task:
        scan_parts.append(f"task-{task}")
    if acq:
        scan_parts.append(f"acq-{acq}")
    if run:
        try:
            scan_parts.append(f"run-{str(int(float(run)))}")
        except ValueError:
            scan_parts.append(f"run-{run}")

    scan_pattern = "_".join(scan_parts)
    if scan_pattern:
        scan_pattern += "_"

    # Build regex pattern to remove from file_name
    pattern = f"{sub_ses}_" + scan_pattern
    resource_name = row["file_name"].replace(pattern, "")
    resource_name = resource_name.replace(f"{sub_ses}_", "")
    return resource_name

def get_rows_by_resource_name(resource_name, datatype, nii_gz_files):
    # Ensure nii_gz_files is a DataFrame and access the correct column
    if isinstance(nii_gz_files, pd.DataFrame):
        # Filter rows using the fnmatch pattern and datatype match if datatype is provided
        if datatype:
            rows = nii_gz_files[
                nii_gz_files['resource_name'].apply(lambda x: fnmatch(x, resource_name)) &
                (nii_gz_files['datatype'] == datatype)
            ]
        else:
            rows = nii_gz_files[
                nii_gz_files['resource_name'].apply(lambda x: fnmatch(x, resource_name))
            ]
        
        if len(rows) == 0:
            message = f"NOT FOUND: {resource_name} with datatype: {datatype}"
            logger.error(message=message)
            return None
        return rows
    else:
        message = "nii_gz_files is not a DataFrame"
        logger.error(message=message)
        return None

# check file_path and drop the ones that are higher dimensions for now
def is_3d_or_4d(file_path):
    dim = len(nib.load(file_path).shape)
    if dim > 4:
        file_name = os.path.basename(file_path).split(".")[0]
        message = f"NOT 3D: {file_name} \n its {dim}D"
        logger.error(message=message)
        message = f"Skipping for now ...."
        logger.error(message=message)

        return False
    return True

def get_scan(row):
    task = row.get("task", "")
    acq = row.get("acq", "")
    run = row.get("run", "")

    # Handle missing or NaN values
    task_str = f"task-{task}" if task and str(task).strip() and str(task).lower() != "nan" else ""
    acq_str = f"acq-{acq}" if acq and str(acq).strip() and str(acq).lower() != "nan" else ""

    try:
        run_str = f"run-{str(int(float(run)))}" if run and str(run).strip() and str(run).lower() != "nan" else ""
        
    except ValueError:
        run_str = f"run-{run}" if run and str(run).strip() and str(run).lower() != "nan" else ""

    # Combine non-empty parts
    parts = [p for p in [task_str, acq_str, run_str] if p]
    return "_".join(parts)

def get_sub_ses(row):
    sub = row["sub"]
    ses = row["ses"] if row["ses"] != "" else False
    return f"sub-{sub}_ses-{ses}" if ses else f"sub-{sub}"

def gen_filename(res1_row, res2_row=None):
    scan = res1_row["scan"] + "_"
    if res2_row is not None:
        return f"sub-{res1_row['sub']}_ses-{res1_row['ses']}_{scan + res1_row['resource_name']} overlaid on {res2_row['resource_name']}"
    else:
        return f"sub-{res1_row['sub']}_ses-{res1_row['ses']}_{scan + res1_row['resource_name']}"

def create_directory(sub, ses, base_dir):
    sub_dir = os.path.join(base_dir, sub, ses)
    os.makedirs(sub_dir, exist_ok=True)
    return sub_dir

def generate_plot_path(sub_dir, file_name):
    return os.path.join(sub_dir, f"{file_name}.png")

def process_row(row, nii_gz_files, overlay_dir, plots_dir, report):
    image_1 = row.get("output", False)
    image_2 = row.get("underlay", False)
    datatype = row.get("datatype", False)

    resource_name_1 = get_rows_by_resource_name(image_1, datatype, nii_gz_files) if image_1 else None
    resource_name_2 = get_rows_by_resource_name(image_2, False, nii_gz_files) if image_2 else None

    if resource_name_1 is None:
        message = f"NOT FOUND: {image_1}"
        logger.error(message=message)
        report.add_missing_files(image_1)
        return []

    result_rows = []
    seen = set()  # To track duplicates

    for _, res1_row in resource_name_1.iterrows():
        if resource_name_2 is not None:
            result_rows.extend(process_res2_rows(res1_row, resource_name_2, seen, overlay_dir, plots_dir))
        else:
            result_rows.extend(process_single_row(res1_row, seen, plots_dir))

    return result_rows

def process_res2_rows(res1_row, resource_name_2, seen, overlay_dir, plots_dir):
    result_rows = []
    for _, res2_row in resource_name_2.iterrows():
        file_name = gen_filename(res1_row, res2_row)
        if res1_row['space'] == res2_row['space']:
            if file_name not in seen:
                seen.add(file_name)
                sub_dir = create_directory(res1_row['sub'], res1_row['ses'], overlay_dir)
                plot_path = generate_plot_path(sub_dir, file_name)
                result_rows.append(create_result_row(res1_row, res2_row, file_name, overlay_dir, plot_path))
        elif res1_row['space'] == "" or res2_row['space'] == "":
            pass
        else:
            message = f"SPACE MISMATCH while trying to plot .. \n{file_name.split('overlaid on')[0]}\nover\n{file_name.split(' overlaid on ')[1]}\n{res1_row['space']} != {res2_row['space']}"
            logger.info(message=message)

    if len(result_rows) == 0:
        message = f"MATCHING SPACE NOT-FOUND to plot {res1_row['resource_name']} over {resource_name_2['resource_name'].tolist()}"
        logger.error(message=message)
        file_name = gen_filename(res1_row) + " *SPACE MISMATCH TO OVERLAY!*"
        if file_name not in seen:
            seen.add(file_name)
            sub_dir = create_directory(res1_row['sub'], res1_row['ses'], plots_dir)
            plot_path = generate_plot_path(sub_dir, file_name)
            result_rows.append(create_result_row(res1_row, None, file_name, plots_dir, plot_path))
    return result_rows

def process_single_row(res1_row, seen, plots_dir):
    result_rows = []
    file_name = gen_filename(res1_row)
    if file_name not in seen:
        seen.add(file_name)
        sub_dir = create_directory(res1_row['sub'], res1_row['ses'], plots_dir)
        plot_path = generate_plot_path(sub_dir, file_name)
        result_rows.append(create_result_row(res1_row, None, file_name, plots_dir, plot_path))
    return result_rows

def create_result_row(res1_row, res2_row, file_name, plots_dir, plot_path):
    return {
        "sub": res1_row["sub"],
        "ses": res1_row["ses"],
        "file_path_1": res1_row["file_path"],
        "file_path_2": res2_row["file_path"] if res2_row is not None else None,
        "file_name": file_name,
        "plots_dir": plots_dir,
        "plot_path": plot_path,
        "datatype": res1_row["datatype"],
        "resource_name": res1_row["resource_name"],
        "space": res1_row["space"],
        "scan": res1_row["scan"],
        "json": res1_row["json"]
    }

def fill_space(row):
    space = row.get("space", "")
    datatype = row.get("datatype", "")
    if space == "":
        if datatype == "anat":
            return "T1w"
        elif datatype == "func":
            return "bold"
    return space



KEYS_TO_REMOVE = {"CpacConfig", "CpacProvenance", "CpacConfigHash"}

def remove_keys(d, keys_to_remove):
    if isinstance(d, dict):
        return {k: remove_keys(v, keys_to_remove)
                for k, v in d.items() if k not in keys_to_remove}
    elif isinstance(d, list):
        return [remove_keys(i, keys_to_remove) for i in d]
    return d

def parse_json_column(val):
    """
    Parse a JSON column value into a cleaned Python dict.
    Handles nested dicts/lists and removes unwanted keys.
    """
    try:
        # Try to parse string to dict/list
        if isinstance(val, str):
            parsed = ast.literal_eval(val)
        else:
            parsed = val
        cleaned = remove_keys(parsed, KEYS_TO_REMOVE)
        return cleaned  # returns a dict or list, not a string
    except Exception as e:
        print(f"Error parsing JSON column: {e}")
        return {}


def flatten_json_collapse_lists(d, parent_key='', sep='-'):
    """
    Flatten a nested dict for display, collapsing lists into comma-separated strings.
    """
    items = []
    if isinstance(d, dict):
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_json_collapse_lists(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Collapse list to comma-separated string if not list of dicts
                if all(not isinstance(i, dict) for i in v):
                    items.append((new_key, ", ".join(str(i) for i in v)))
                else:
                    # If list of dicts, flatten each dict
                    for idx, item in enumerate(v):
                        items.extend(flatten_json_collapse_lists(item, f"{new_key}[{idx}]", sep=sep).items())
            else:
                items.append((new_key, v))
    else:
        items.append((parent_key, d))
    return dict(items)

def clean_and_flatten_json_column(val):
    """
    Parse, clean (remove unwanted keys), and flatten the JSON column value into a 1-level dict,
    collapsing lists into comma-separated strings.
    """
    try:
        cleaned = parse_json_column(val)
        flat = flatten_json_collapse_lists(cleaned)
        return flat  # returns a flat dict
    except Exception as e:
        print(f"Error cleaning and flattening JSON column: {e}")
        return {}
