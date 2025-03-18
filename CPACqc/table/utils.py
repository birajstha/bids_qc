import pandas as pd
import os
import argparse
from multiprocessing import Pool
from tqdm import tqdm
from functools import lru_cache
import tempfile

import nibabel as nib
from nibabel.orientations import io_orientation, ornt2axcodes
from colorama import Fore, Style, init

from CPACqc.plotting.plot import run
from CPACqc.bids2table._b2t import bids2table
from CPACqc.logging.log import logger

import json
import re

def get_file_info(file_path):
    img = nib.load(file_path)
    resolution = tuple(float(x) for x in img.header.get_zooms())
    dimension = tuple(int(x) for x in img.shape)
    
    affine = img.affine
    orientation =  "".join(ornt2axcodes(io_orientation(affine))) + " @nibabel"
    
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

def gen_resource_name(row):
    sub = row["sub"]
    ses = row["ses"] if row["ses"] != "" else False

    sub_ses = f"sub-{sub}_ses-{ses}" if ses else f"sub-{sub}"

    task = row["task"] if row["task"] != "" else False
    run = row["run"] if row["run"] != "" else False
    
    # Create a flexible pattern for the scan part
    scan = f"task-{task}_run-\\d*_" if task and run else ""
    
    # Use regular expression to replace the pattern
    pattern = re.escape(f"{sub_ses}_") + scan
    resource_name = re.sub(pattern, "", row["file_name"])
    
    return resource_name

# add a utility function to return rows provided a resource_name
def get_rows_by_resource_name(resource_name, nii_gz_files):
    # Ensure nii_gz_files is a DataFrame and access the correct column
    if isinstance(nii_gz_files, pd.DataFrame):
        rows = nii_gz_files[nii_gz_files['resource_name'].str.endswith(resource_name)]
        if len(rows) == 0:
            logger.error(f"NOT FOUND: {resource_name}")
            return None
        return rows
    else:
        logger.error("nii_gz_files is not a DataFrame")
        return None

# check file_path and drop the ones that are higher dimensions for now
def is_3d_or_4d(file_path):
    dim = len(nib.load(file_path).shape)
    if dim > 4:
        file_name = os.path.basename(file_path).split(".")[0]
        logger.error(f"NOT 3D: {file_name} \n its {dim}D")
        logger.error(f"Skipping for now ....")
        return False
    return True

def get_scan(row):
    task = row["task"] if row["task"]  else False
    run = int(row["run"]) if row["run"]  else False
    return f"task-{task}_run-{run}" if task and run else ""

def get_sub_ses(row):
    sub = row["sub"]
    ses = row["ses"] if row["ses"] != "" else False
    return f"sub-{sub}_ses-{ses}" if ses else f"sub-{sub}"

def gen_filename(res1_row, res2_row=None):
    scan = f"task-{res1_row['task']}_run-{int(res1_row['run'])}_" if res1_row['task'] and res1_row['run'] else ""
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

def process_row(row, nii_gz_files, overlay_dir, plots_dir):
    image_1 = row.get("output", False)
    image_2 = row.get("underlay", False)

    resource_name_1 = get_rows_by_resource_name(image_1, nii_gz_files) if image_1 else None
    resource_name_2 = get_rows_by_resource_name(image_2, nii_gz_files) if image_2 else None

    if resource_name_1 is None:
        logger.error(f"NOT FOUND: {image_1}")
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
        else:
            logger.info(f"SPACE MISMATCH while trying to plot .. \n{file_name.split('overlaid on')[0]}\nover\n{file_name.split(' overlaid on ')[1]}\n{res1_row['space']} != {res2_row['space']}")
    if len(result_rows) == 0:
        logger.error(f"MATCHING SPACE NOT-FOUND to plot {res1_row['resource_name']} over {resource_name_2['resource_name'].tolist()}")
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
        "scan": res1_row["scan"]
    }

def parse_bids(base_dir, sub=None, workers=8):
    print(Fore.YELLOW + "Parsing BIDS directory..." + Style.RESET_ALL)
    if logger: 
        logger.info("Parsing BIDS directory...")

    df = bids2table(base_dir, subject=sub, workers=workers).flat
    return df

def run_wrapper(args):
    return run(*args)

def fill_space(row):
    if row["space"] == "":
        if row["datatype"] == "anat":
            return "T1w"
        elif row["datatype"] == "func":
            return "bold"
    return row["space"]
