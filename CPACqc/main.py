import pandas as pd
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

from bids2table import bids2table
import nibabel as nib
from colorama import Fore, Style, init
import logging

from CPACqc.utils import *
from CPACqc.plot import run

def setup_logger(qc_dir):
    # setup logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Create a file handler
    log_file = os.path.join(qc_dir, 'qc.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    
    return logger

def main(bids_dir, qc_dir, config=False, sub=None, n_procs=8):
    os.makedirs(qc_dir, exist_ok=True)
    logger = setup_logger(qc_dir)
    
    logger.info(f"Running QC with nprocs {n_procs}...")
    
    csv_file = os.path.join(qc_dir, "df.csv")

    plots_dir = os.path.join(qc_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    overlay_dir = os.path.join(qc_dir, "overlays")
    os.makedirs(overlay_dir, exist_ok=True)

    if sub:
        if isinstance(sub, str):
            sub = [sub]

    df = parse_bids(bids_dir, sub, workers=n_procs, logger=logger)
    
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

    nii_gz_files = nii_gz_files[nii_gz_files.file_path.apply(lambda x: is_3d_or_4d(x, logger))]

    # save nii_gz_files to csv
    nii_gz_files_csv_path = os.path.join(qc_dir, "nii_gz_files.csv")
    nii_gz_files.to_csv(nii_gz_files_csv_path, index=False)

    # for rows in overlay_csv find the resource_name and get the rows
    if config:
        overlay_df = pd.read_csv(config)
        overlay_df = overlay_df.fillna(False)
        results = overlay_df.apply(lambda row: process_row(row, nii_gz_files, overlay_dir, plots_dir, logger), axis=1).tolist()

        # Flatten the list of lists
        results = [item for sublist in results for item in sublist]

        # Create a DataFrame from the results
        result_df = pd.DataFrame(results)
    else:
        result_df = nii_gz_files.copy()
        result_df['file_path_1'] = nii_gz_files['file_path']
        result_df['file_path_2'] = None
        result_df['file_name'] = result_df.apply(lambda row: gen_filename(res1_row=row), axis=1)
        result_df['plots_dir'] = plots_dir
        result_df['plot_path'] = result_df.apply(lambda row: generate_plot_path(create_directory(row['sub'], row['ses'], row['plots_dir']), row['file_name']), axis=1)
        
        columns_to_keep = ['sub', 'ses', 'file_path_1', 'file_path_2', 'file_name', 'plots_dir', 'plot_path']
        result_df = result_df[columns_to_keep].copy()

    result_df['relative_path'] = result_df.apply(lambda row: os.path.relpath(row['plot_path'], qc_dir), axis=1)
    result_df['file_info'] = result_df.apply(lambda row: get_file_info(row['file_path_1']), axis=1)
    
    # save the result_df to csv
    result_df_csv_path = os.path.join(qc_dir, "results.csv")
    if os.path.exists(result_df_csv_path):
        result_df.to_csv(result_df_csv_path, mode='a', header=False, index=False)
    else:
        result_df.to_csv(result_df_csv_path, index=False)
    
    args = [
        (
            row['sub'], 
            row['ses'],  
            row['file_path_1'],
            row['file_path_2'], 
            row['file_name'],
            row['plots_dir'],
            row['plot_path'],
            logger
        ) 
        for _, row in result_df.iterrows()
    ]

    not_plotted = []
    # Use concurrent.futures to process each row with the specified number of processes
    with ProcessPoolExecutor(max_workers=n_procs) as executor:
        futures = {executor.submit(run_wrapper, arg): arg for arg in args}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing ..."):
            try:
                future.result()
            except Exception as e:
                if "terminated abruptly" in str(e):
                    print(Fore.RED + f"Error processing {futures[future]}: {e}\n Try with lower number of processes" + Style.RESET_ALL)
                logger.error(f"Error processing {futures[future]}: {e}, Try with a lower number of processes")
                not_plotted.append(futures[future])
    return not_plotted
    
if __name__ == "__main__":
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process BIDS directory and generate QC plots.")
    parser.add_argument("--bids_dir", required=True, help="Path to the BIDS directory")
    parser.add_argument("--qc_dir", required=True, help="Path to the QC output directory")
    parser.add_argument("--config", required=False, help="Config file")
    parser.add_argument("--n_procs", type=int, default=10, help="Number of processes to use for multiprocessing")

    args = parser.parse_args()
    main(args.bids_dir, args.qc_dir, args.config, args.n_procs)