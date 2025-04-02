from CPACqc.main import main
import os
import shutil
from colorama import Fore, Style
import pkg_resources
from CPACqc import __version__  # Import the version number
import argparse
import pandas as pd

class StoreTrueOrString(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            setattr(namespace, self.dest, True)
        else:
            setattr(namespace, self.dest, values)

def run():

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process BIDS directory and generate QC plots.")
    parser.add_argument("-d", "--bids_dir", required=True, help="Path to the BIDS directory")
    parser.add_argument("-o", "--qc_dir", required=False, help="Path to the QC output directory")
    parser.add_argument("-c", "--config", required=False, help="Config file")
    parser.add_argument("-s", "--sub", nargs='+', required=False, help="Specify subject/participant label(s) to process")
    parser.add_argument("-n", "--n_procs", type=int, default=8, help="Number of processes to use for multiprocessing")
    parser.add_argument("-v", "--version", action='version', version=f'%(prog)s {__version__}', help="Show the version number and exit")
    
    args = parser.parse_args()

    if args.bids_dir is None:
        print(Fore.RED + "Please specify the BIDS directory.")
        print(Style.RESET_ALL)
        return
    
    if args.qc_dir is None:
        args.qc_dir = os.path.join(os.getcwd(), '.temp_qc')
        print(Fore.YELLOW + f"Output directory not specified. Saving output to {args.qc_dir}")
        print(Style.RESET_ALL)


    if args.config is not None:
        if not os.path.exists(args.config):
            print(Fore.RED + f"Config file not found: {args.config}")
            print(Style.RESET_ALL)
            return

        if not os.path.isfile(args.config):
            print(Fore.RED + f"Config file is not a file: {args.config}")
            print(Style.RESET_ALL)
            return

        if not args.config.endswith('.csv'):
            print(Fore.RED + f"Config file is not a CSV file: {args.config}")
            print(Style.RESET_ALL)
            return
            
        # check if it has output and underlay columns
        config_df = pd.read_csv(args.config)
        if 'output' not in config_df.columns:
            print(Fore.RED + f"Config file does not have output column: {args.config}")
            print(Style.RESET_ALL)
            return

    if args.config is None:
        args.config = pkg_resources.resource_filename('CPACqc', 'overlay/overlay.csv')
        print(Fore.YELLOW + f"Config file not specified. Using default config file: {args.config}")
        print(Style.RESET_ALL)
        
    try:
        # Create the QC output directory if it doesn't exist
        os.makedirs(args.qc_dir, exist_ok=True)

    except Exception as e:
        print(f"Error !! : {e}")
        return  # Exit the function if an error occurs

    not_plotted = main(args.bids_dir, args.qc_dir, args.config, args.sub, args.n_procs)


    if ".temp_qc" in args.qc_dir:
        # remove the qc_dir if not generating HTML report
        print(Fore.YELLOW + f"Removing the QC output directory: {args.qc_dir}")
        print(Style.RESET_ALL)
        shutil.rmtree(args.qc_dir)
    else:
        # Combine all the CSVs inside qc_dir/csv into one CSV and name it results.csv
        csv_dir = os.path.join(args.qc_dir, 'csv')
        overlays_dir = os.path.join(args.qc_dir, 'overlays')
        plots_dir = os.path.join(args.qc_dir, 'plots')
        
        # List of directories to remove
        dirs_to_remove = [csv_dir, overlays_dir, plots_dir]
        
        for directory in dirs_to_remove:
            try:
                shutil.rmtree(directory)
            except FileNotFoundError:
                # Skip if the directory does not exist
                continue
            except Exception as e:
                print(f"Error removing directory {directory}: {e}")

    if len(not_plotted) > 0:
        print(Fore.RED + "Some files were not plotted. Please check the log for details.")
    else:
        print(Fore.GREEN + "All files were successfully plotted.")
    print(Style.RESET_ALL)