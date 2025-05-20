# CPACqc/cli.py

import argparse
from colorama import Fore, Style
from CPACqc.core.QCPipeline import QCPipeline
from CPACqc.core.validation import validate_args
from CPACqc import __version__, __author__, __email__, __description__

def get_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    version_str = (
        f"{Fore.GREEN}CPACqc version: {__version__}{Style.RESET_ALL}"
    )
    parser = argparse.ArgumentParser(description="Process BIDS directory and generate QC plots.")
    parser.add_argument("-d", "--bids_dir", required=True, help="Path to the BIDS directory")
    parser.add_argument("-o", "--qc_dir", required=False, help="Path to the QC output directory")
    parser.add_argument("-c", "--config", required=False, help="Config file")
    parser.add_argument("-s", "--sub", nargs='+', required=False, help="Specify subject/participant label(s) to process")
    parser.add_argument("-n", "--n_procs", type=int, default=8, help="Number of processes to use for multiprocessing")
    parser.add_argument("-v", "--version", action='version', version=version_str, help="Show the version number and exit")

    return parser.parse_args()


def run():
    """
    Main function to execute the command line interface for processing BIDS directories.
    """
    args = get_args()

    # Validate the arguments
    try:
        args = validate_args(args)
    except ValueError as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        return
    
    pipeline = QCPipeline(args)
    pipeline.run()


if __name__ == "__main__":
    run()