import pandas as pd
import os
import argparse
from multiprocessing import Pool
from tqdm import tqdm
from functools import lru_cache
import tempfile

import nibabel as nib
from colorama import Fore, Style, init

from CPACqc.plot import run
from CPACqc.bids2table._b2t import bids2table
import json
import re

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def get_file_info(file_path):
    img = nib.load(file_path)
    resolution = tuple(float(x) for x in img.header.get_zooms())
    dimension = tuple(int(x) for x in img.shape)
    if len(dimension) == 4:
        # get TR info
        tr = float(img.header.get_zooms()[3])
        nos_tr = str(int(img.shape[-1]))
    else:
        tr = None
        nos_tr = None
    return json.dumps({"resolution": resolution, "dimension": dimension, "tr": tr, "nos_tr": nos_tr})

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

def parse_bids(base_dir, sub=None, workers=8, logger=None):
    print(Fore.YELLOW + "Parsing BIDS directory..." + Style.RESET_ALL)
    if logger: 
        logger.info("Parsing BIDS directory...")

    df = bids2table(base_dir, subject=sub, workers=workers).flat
    return df

def run_wrapper(args):
    return run(*args)

def make_pdf(qc_dir, pdf_name="report.pdf"):
    print(Fore.YELLOW + "Generating PDF report..." + Style.RESET_ALL)

    # Read the CSV file
    csv_data = pd.read_csv(os.path.join(qc_dir, "results.csv"))

    # Handle .pdf in pdf_name
    if pdf_name[-4:] != ".pdf":
        pdf_name += ".pdf"

    pdf_path = os.path.join(qc_dir, pdf_name)
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Add CPAC logo and description to the front page
    logo_path = 'https://avatars.githubusercontent.com/u/2230402?s=200&v=4'  # Adjust the path as needed
    logo_img = ImageReader(logo_path)
    logo_width = 150  # Adjust the logo width
    logo_height = 150  # Adjust the logo height
    c.drawImage(logo_img, (width - logo_width) / 2, (height - logo_height) / 2, width=logo_width, height=logo_height)
    c.setFont("Helvetica", 20)
    c.drawString(70, height - 130, "CPAC Quality Control Report")
    c.setFont("Helvetica", 12)

    # Add an initial page to skip the first page
    c.showPage()

    y_position = height - 30  # Start at the top of the new page

    # Get unique subjects and sort them in ascending order
    subjects = sorted(set(csv_data['sub']))

    # Add all images to the PDF, grouped by subject
    for subject in subjects:
        subject_images = csv_data[csv_data['sub'] == subject]

        if not subject_images.empty:
            for _, image_data in subject_images.iterrows():
                image_path = os.path.join(qc_dir, image_data['relative_path'])
                if os.path.exists(image_path):
                    img = ImageReader(image_path)
                    max_img_width = width - 20  # Adjust the max width to fit the page
                    max_img_height = height / 2  # Adjust the max height to fit the page

                    # Preserve aspect ratio
                    img_width, img_height = img.getSize()
                    aspect_ratio = img_width / img_height
                    if aspect_ratio > 1:
                        img_width = max_img_width
                        img_height = img_width / aspect_ratio
                    else:
                        img_height = max_img_height
                        img_width = img_height * aspect_ratio

                    # Check if the image fits on the current page, otherwise add a new page
                    if y_position - img_height - 80 < 0:  # Adjusted to account for additional text and white space
                        c.showPage()
                        y_position = height - 30  # Reset y_position for the new page

                    # Add the image to the PDF
                    c.drawImage(img, (width - img_width) / 2, y_position - img_height, width=img_width, height=img_height)
                    c.setFont("Helvetica", 10)  # Use smaller font for the file name
                    label = f"{image_data['sub']}_{image_data['file_name']}"
                    c.drawString(10, y_position - img_height - 10, label)

                    # Add file information under the image label
                    file_info = json.loads(image_data['file_info'])
                    file_info_text = [
                        f"Dimensions: {file_info['dimension']}",
                        f"Resolution: {[round(res, 2) for res in file_info['resolution']]}"
                    ]

                    if file_info['tr'] is not None:
                        file_info_text.append(f"TR: {file_info['tr']}")

                    if file_info['nos_tr'] is not None:
                        file_info_text.append(f"No of TRs: {file_info['nos_tr']}")

                    c.setFont("Helvetica", 8)  # Use smaller font for the file info
                    for i, line in enumerate(file_info_text):
                        c.drawString(10, y_position - img_height - 25 - (i * 10), line)

                    # Move to the next row after each image
                    y_position -= img_height + 80  # Adjusted to account for additional text and white space

    # Save the PDF
    c.save()
    print(Fore.GREEN + "PDF report generated successfully." + Style.RESET_ALL)