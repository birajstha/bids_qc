import pandas as pd
import os
import pandas as pd
import os
import argparse

from CPACqc.table.table import preprocess
from CPACqc.table.utils import *
from CPACqc.multiprocessing.multiprocessing_utils import run_multiprocessing
from CPACqc.report.pdf import make_pdf
from CPACqc.logging.log import logger

def main(bids_dir, qc_dir, config=False, sub=None, n_procs=8, pdf=False):
    os.makedirs(qc_dir, exist_ok=True)
    
    logger.info(f"Running QC with nprocs {n_procs}...")
    
    # Create necessary directories
    for directory in ["plots", "overlays", "csv"]:
        os.makedirs(os.path.join(qc_dir, directory), exist_ok=True)
    
    plots_dir = os.path.join(qc_dir, "plots")
    overlay_dir = os.path.join(qc_dir, "overlays")
    csv_dir = os.path.join(qc_dir, "csv")

    if sub and isinstance(sub, str):
        sub = [sub]

    df = parse_bids(bids_dir, sub=sub, workers=n_procs)
    
    nii_gz_files = preprocess(df)

    # split the df into different df based on unique sub_ses
    sub_ses = nii_gz_files["sub_ses"].unique()
    no_sub_ses = len(sub_ses)
    if no_sub_ses == 0:
        logger.error("No subjects found.")
        print(Fore.RED + "No subjects found." + Style.RESET_ALL)
        return

    not_plotted = []
    # different df for each sub_ses
    for index, sub_ses in enumerate(sub_ses):
        index = index + 1
        sub_df = nii_gz_files[nii_gz_files["sub_ses"] == sub_ses]

        print(Fore.YELLOW + f"Processing {sub_ses} ({index}/{no_sub_ses})..." + Style.RESET_ALL)
        logger.info(f"Processing {sub_ses} ({index}/{no_sub_ses})...")

        overlay_df = pd.read_csv(config).fillna(False)
        results = overlay_df.apply(lambda row: process_row(row, sub_df, overlay_dir, plots_dir), axis=1).tolist()
        results = [item for sublist in results for item in sublist]  # Flatten the list of lists
        result_df = pd.DataFrame(results)
        # add missing rows to result_df from sub_df look for file_path in sub_df and file_path_1 in result_df
        missing_rows = sub_df.loc[~sub_df['file_path'].isin(result_df['file_path_1'])].copy()
        missing_rows['file_path_1'] = missing_rows['file_path']
        missing_rows['file_path_2'] = None
        missing_rows['file_name'] = missing_rows.apply(lambda row: gen_filename(res1_row=row), axis=1)
        missing_rows['plots_dir'] = plots_dir
        missing_rows['plot_path'] = missing_rows.apply(lambda row: generate_plot_path(create_directory(row['sub'], row['ses'], row['plots_dir']), row['file_name']), axis=1)
        missing_rows = missing_rows[['sub', 'ses', 'file_path_1', 'file_path_2', 'file_name', 'plots_dir', 'plot_path', 'datatype', 'resource_name', 'space', 'scan']].copy()
        result_df = pd.concat([result_df, missing_rows], ignore_index=True)
        result_df['relative_path'] = result_df.apply(lambda row: os.path.relpath(row['plot_path'], qc_dir), axis=1)
        result_df['file_info'] = result_df.apply(lambda row: get_file_info(row['file_path_1']), axis=1)
        
        result_df_csv_path = os.path.join(csv_dir, f"{sub_ses}_results.csv")
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

        not_plotted += run_multiprocessing(run_wrapper, args, n_procs)



        if pdf:
            try:
                make_pdf(result_df, qc_dir, sub_ses, overlay_df=overlay_df if config else None)
            except Exception as e:
                logger.error(f"Error generating PDF: {e}")
                print(Fore.RED + f"Error generating PDF: {e}" + Style.RESET_ALL)

    return not_plotted
    
if __name__ == "__main__":
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process BIDS directory and generate QC plots.")
    parser.add_argument("-d", "--bids_dir", required=True, help="Path to the BIDS directory")
    parser.add_argument("-o", "--qc_dir", required=True, help="Path to the QC output directory")
    parser.add_argument("-c", "--config", required=False, help="Config file")
    parser.add_argument("-s", "--sub", nargs='+', required=False, help="Specify subject/participant label(s) to process")
    parser.add_argument("-n", "--n_procs", type=int, default=8, help="Number of processes to use for multiprocessing")
    parser.add_argument("-v", "--version", action='version', version=f'%(prog)s {__version__}', help="Show the version number and exit")
    parser.add_argument("-pdf", "--pdf", required=False, help="Generate PDF report")

    args = parser.parse_args()
    main(args.bids_dir, args.qc_dir, args.config, args.sub, args.n_procs, args.pdf)