import pandas as pd
import os
import argparse
from multiprocessing import Pool
from tqdm import tqdm
from functools import lru_cache
import tempfile

from bids2table import bids2table
import nibabel as nib
from colorama import Fore, Style, init

from CPACqc.plot import run
import json
import re

def get_file_info(file_path):
    img = nib.load(file_path)
    resolution = tuple(float(x) for x in img.header.get_zooms())
    dimension = tuple(int(x) for x in img.shape)
    if len(dimension) == 4:
        # get TR info
        tr = float(img.header.get_zooms()[3])
    else:
        tr = None
    return json.dumps({"resolution": resolution, "dimension": dimension, "tr": tr})

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
def get_rows_by_resource_name(resource_name, nii_gz_files, logger):
    # get all rows that have the resource_name
    rows = nii_gz_files[nii_gz_files.resource_name == resource_name]
    if len(rows) == 0:
        logger.error(f"NOT FOUND: {resource_name}")
        return None
    return rows

# check file_path and drop the ones that are higher dimensions for now
def is_3d_or_4d(file_path, logger):
    dim = len(nib.load(file_path).shape)
    if dim > 4:
        file_name = os.path.basename(file_path).split(".")[0]
        logger.error(f"NOT 3D: {file_name} \n its {dim}D")
        logger.error(f"Skipping for now ....")
        return False
    return True

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

def process_row(row, nii_gz_files, overlay_dir, plots_dir, logger):
    image_1 = row.get("image_1", False)
    image_2 = row.get("image_2", False)

    resource_name_1 = get_rows_by_resource_name(image_1, nii_gz_files, logger) if image_1 else None
    resource_name_2 = get_rows_by_resource_name(image_2, nii_gz_files, logger) if image_2 else None

    if resource_name_1 is None:
        logger.error(f"NOT FOUND: {image_1}")
        return []

    result_rows = []
    seen = set()  # To track duplicates

    for _, res1_row in resource_name_1.iterrows():
        if resource_name_2 is not None:
            for _, res2_row in resource_name_2.iterrows():
                file_name = gen_filename(res1_row, res2_row)
                if file_name not in seen:
                    seen.add(file_name)
                    sub_dir = create_directory(res1_row['sub'], res1_row['ses'], overlay_dir)
                    plot_path = generate_plot_path(sub_dir, file_name)
                    result_rows.append({
                        "sub": res1_row["sub"],
                        "ses": res1_row["ses"],
                        "file_path_1": res1_row["file_path"],
                        "file_path_2": res2_row["file_path"],
                        "file_name": file_name,
                        "plots_dir": overlay_dir,
                        "plot_path": plot_path
                    })
        else:
            file_name = gen_filename(res1_row)
            if file_name not in seen:
                seen.add(file_name)
                sub_dir = create_directory(res1_row['sub'], res1_row['ses'], plots_dir)
                plot_path = generate_plot_path(sub_dir, file_name)
                result_rows.append({
                    "sub": res1_row["sub"],
                    "ses": res1_row["ses"],
                    "file_path_1": res1_row["file_path"],
                    "file_path_2": None,
                    "file_name": file_name,
                    "plots_dir": plots_dir,
                    "plot_path": plot_path
                })

    return result_rows

@lru_cache(maxsize=None)
def parse_bids(base_dir, sub=None, workers=8, logger=None):
    print(Fore.YELLOW + "Parsing BIDS directory..." + Style.RESET_ALL)
    if logger: 
        logger.info("Parsing BIDS directory...")
    df = bids2table(base_dir, subject=sub, workers=workers).flat
    return df

def run_wrapper(args):
    return run(*args)