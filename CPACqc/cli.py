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
    parser.add_argument("-pdf", "--pdf", nargs='?', const=True, action=StoreTrueOrString, default=True, help="Generate PDF report (default: 'report')")
    parser.add_argument("-html", "--html", action='store_true', help="Generate HTML report")
    
    args = parser.parse_args()

    if args.bids_dir is None:
        print(Fore.RED + "Please specify the BIDS directory.")
        print(Style.RESET_ALL)
        return
    
    if args.qc_dir is None:
        args.qc_dir = os.path.join(os.getcwd(), '.temp_qc')
        print(Fore.YELLOW + f"Output directory not specified. Saving output to {args.qc_dir}")
        print(Style.RESET_ALL)

    if args.pdf is True:
        args.pdf = "report"

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

        if args.html:
            # Locate the templates directory within the package
            templates_dir = pkg_resources.resource_filename('CPACqc', 'templates')

            # Copy only the index.html file from the templates directory to the QC output directory
            src_file = os.path.join(templates_dir, 'index.html')
            dest_file = os.path.join(args.qc_dir, 'index.html')
            shutil.copy2(src_file, dest_file)

    except Exception as e:
        print(f"Error !! : {e}")
        return  # Exit the function if an error occurs

    not_plotted = main(args.bids_dir, args.qc_dir, args.config, args.sub, args.n_procs, args.pdf)

    if not args.html:
        # remove the qc_dir if not generating HTML report
        print(Fore.YELLOW + f"Removing the QC output directory: {args.qc_dir}")
        print(Style.RESET_ALL)
        shutil.rmtree(args.qc_dir)
    else:
        # combine all the csvs inside qc_dir/csv into one csv and name it results.csv
        csv_dir = os.path.join(args.qc_dir, 'csv')
        if os.path.exists(csv_dir):
            # Combine all the csv files into one
            combined_csv = os.path.join(args.qc_dir, 'results.csv')
            combined_df = pd.concat([pd.read_csv(os.path.join(csv_dir, f)) for f in os.listdir(csv_dir) if f.endswith('.csv')])
            combined_df.to_csv(combined_csv, index=False)
        else:
            print(Fore.RED + "No CSV files found in the QC output directory. Please check the log for details.")
            print(Style.RESET_ALL)
            return
        # Rename the qc_dir to results
        new_qc_dir = os.path.join(os.getcwd(), 'results')
        print(Fore.YELLOW + f"Creating HTML report in results dir: {new_qc_dir}")
        print(Style.RESET_ALL)
        
        # Check if the results directory already exists and remove it if it does
        if os.path.exists(new_qc_dir):
            shutil.rmtree(new_qc_dir)
        
        shutil.move(args.qc_dir, new_qc_dir)
        print(Fore.YELLOW + "Done.")

    if len(not_plotted) > 0:
        print(Fore.RED + "Some files were not plotted. Please check the log for details.")
    else:
        print(Fore.GREEN + "All files were successfully plotted.")
    print(Style.RESET_ALL)