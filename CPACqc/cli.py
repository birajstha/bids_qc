from CPACqc.main import main
import os
import shutil
from colorama import Fore, Style
import pkg_resources
from CPACqc import __version__  # Import the version number

def run():
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process BIDS directory and generate QC plots.")
    parser.add_argument("-d", "--bids_dir", required=True, help="Path to the BIDS directory")
    parser.add_argument("-o", "--qc_dir", required=True, help="Path to the QC output directory")
    parser.add_argument("-c", "--config", required=False, help="Config file")
    parser.add_argument("-s", "--sub", nargs='+', required=False, help="Specify subject/participant label(s)")
    parser.add_argument("-n", "--n_procs", type=int, default=8, help="Number of processes to use for multiprocessing")
    parser.add_argument("-v", "--version", action='version', version=f'%(prog)s {__version__}', help="Show the version number and exit")
    
    args = parser.parse_args()
    
    try:
        # Create the QC output directory if it doesn't exist
        os.makedirs(args.qc_dir, exist_ok=True)

        # Locate the templates directory within the package
        templates_dir = pkg_resources.resource_filename('CPACqc', 'templates')
        # Copy only the index.html file from the templates directory to the QC output directory
        src_file = os.path.join(templates_dir, 'index.html')
        dest_file = os.path.join(args.qc_dir, 'index.html')
        shutil.copy2(src_file, dest_file)
    except Exception as e:
        print(f"Error copying templates: {e}")
        return  # Exit the function if an error occurs

    not_plotted = main(args.bids_dir, args.qc_dir, args.config, args.sub, args.n_procs)
    if len(not_plotted) > 0:
        print(Fore.RED + "Some files were not plotted. Please check the log for details.")
    else:
        print(Fore.GREEN + "All files were successfully plotted.")
    print(Style.RESET_ALL)