import pandas as pd
import os
import argparse

from CPACqc.core.utils import *
from CPACqc.utils.multiprocessing.multiprocessing_utils import ProcessPoolMultiprocessing
from CPACqc.utils.report.pdf import Report
from CPACqc.core.config import Config
from CPACqc.utils.tabler.bids2table import Bids2TableDetails
from CPACqc.core.entity import Table

def main(args):  
    app_config = Config(
        bids_dir = args.bids_dir,
        qc_dir = args.qc_dir,
        subject_list = args.sub,
        overlay_csv = args.config,
        n_procs = args.n_procs
    )

    app_config.plots_dir = os.path.join(app_config.qc_dir, "plots")
    app_config.overlay_dir = os.path.join(app_config.qc_dir, "overlays")
    app_config.csv_dir = os.path.join(app_config.qc_dir, "csv")
    app_config.make_dirs()

    # Set up logging
    logger = app_config.logger
    logger.info(f"Running QC with nprocs {app_config.n_procs}...")
  
    bids_parser = Bids2TableDetails(
        base_dir=app_config.bids_dir,
        subjects=app_config.subject_list,
        workers=app_config.n_procs
    )

    my_table = Table(bids_parser.get_dataframe())
    nii_gz_files = my_table.processed_table

    
    # split the df into different df based on unique sub_ses
    sub_ses = nii_gz_files["sub_ses"].unique()
    no_sub_ses = len(sub_ses)
    if no_sub_ses == 0:
        print(Fore.RED + "No subjects found." + Style.RESET_ALL)
        return

    not_plotted = []
    # different df for each sub_ses
    for index, sub_ses in enumerate(sub_ses):
        index = index + 1
        sub_df = nii_gz_files[nii_gz_files["sub_ses"] == sub_ses]

        print(Fore.YELLOW + f"Processing {sub_ses} ({index}/{no_sub_ses})..." + Style.RESET_ALL)

        overlay_df = pd.read_csv(app_config.overlay_csv).fillna(False)
        
        # initialize the report
        report = Report(
            qc_dir=app_config.qc_dir,
            sub_ses=sub_ses,
            overlay_df=overlay_df
        )

        results = overlay_df.apply(lambda row: process_row(row, sub_df, app_config.overlay_dir, app_config.plots_dir, report), axis=1).tolist()
        results = [item for sublist in results for item in sublist]  # Flatten the list of lists
        result_df = pd.DataFrame(results)
        if 'file_path_1' not in result_df.columns:
            result_df['file_path_1'] = None
        # add missing rows to result_df from sub_df look for file_path in sub_df and file_path_1 in result_df
        missing_rows = sub_df.loc[~sub_df['file_path'].isin(result_df['file_path_1'])].copy()
        if not missing_rows.empty:
            missing_rows['file_path_1'] = missing_rows['file_path']
            missing_rows['file_path_2'] = None
            missing_rows['file_name'] = missing_rows.apply(lambda row: gen_filename(res1_row=row), axis=1)
            missing_rows['plots_dir'] = app_config.plots_dir
            missing_rows['plot_path'] = missing_rows.apply(lambda row: generate_plot_path(create_directory(row['sub'], row['ses'], row['plots_dir']), row['file_name']), axis=1)
            missing_rows = missing_rows[['sub', 'ses', 'file_path_1', 'file_path_2', 'file_name', 'plots_dir', 'plot_path', 'datatype', 'resource_name', 'space', 'scan']].copy()
            result_df = pd.concat([result_df, missing_rows], ignore_index=True)
        result_df['relative_path'] = result_df.apply(lambda row: os.path.relpath(row['plot_path'], app_config.qc_dir), axis=1)
        result_df['file_info'] = result_df.apply(lambda row: get_file_info(row['file_path_1']), axis=1)
        
        result_df_csv_path = os.path.join(app_config.csv_dir, f"{sub_ses}_results.csv")
        result_df.to_csv(result_df_csv_path, mode='a' if os.path.exists(result_df_csv_path) else 'w', header=not os.path.exists(result_df_csv_path), index=False)
        
        # analyze the result_df and remove the duplicate rows
        result_df = result_df.drop_duplicates(subset=["file_path_1", "file_path_2", "file_name", "plots_dir", "plot_path", "datatype", "resource_name", "space", "scan"], keep="first")
        
        args = [
            (
                row['sub'], 
                row['ses'],  
                row['file_path_1'],
                row['file_path_2'], 
                row['file_name'],
                row['plots_dir'],
                row['plot_path'],
            ) 
            for _, row in result_df.iterrows()
        ]

        multiprocessor = ProcessPoolMultiprocessing()

        not_plotted += multiprocessor.run(run_wrapper, args, app_config.n_procs)


        try:
            report.df = result_df
            report.generate_report()
            report.save_report()
            Report.destroy_instance()

        except Exception as e:
            print(Fore.RED + f"Error generating PDF: {e}" + Style.RESET_ALL)

    return not_plotted
    
def cleanup_qc_dir(qc_dir: str):
    """
    Remove temporary QC directory or unnecessary files after processing.
    """
    if ".temp_qc" in qc_dir:
        print(Fore.YELLOW + f"Removing the QC output directory: {qc_dir}" + Style.RESET_ALL)
        shutil.rmtree(qc_dir)
    else:
        # Remove specific subdirectories from qc_dir
        dirs_to_remove = [
            os.path.join(qc_dir, 'csv'),
            os.path.join(qc_dir, 'overlays'),
            os.path.join(qc_dir, 'plots')
        ]
        for directory in dirs_to_remove:
            try:
                shutil.rmtree(directory)
            except FileNotFoundError:
                continue
            except Exception as e:
                print(Fore.RED + f"Error removing directory {directory}: {e}" + Style.RESET_ALL)