import os
from CPACqc import __version__

def validate_args(args):
    """
    Validate command-line arguments.
    """
    # Check if the BIDS directory exists
    if not os.path.exists(args.bids_dir):
        raise ValueError(f"BIDS directory '{args.bids_dir}' does not exist.")
    
    # Check if the QC output directory exists or create it
    if args.qc_dir:
        os.makedirs(args.qc_dir, exist_ok=True)
    
    # Check if the config file exists
    if args.config and not os.path.exists(args.config):
        raise ValueError(f"Config file '{args.config}' does not exist.")
    
    # Check if the subject list is valid
    if args.sub:
        for sub in args.sub:
            if not isinstance(sub, str):
                raise ValueError(f"Invalid subject label: {sub}. It should be a string.")
            if not sub.startswith("sub-"):
                raise ValueError(f"Invalid subject label format: {sub}. It should start with 'sub-'.")

    # Check if the number of processes is valid
    if args.n_procs <= 0:
        raise ValueError(f"Number of processes '{args.n_procs}' should be a positive integer.")

    
    # return the validated arguments
    return args

