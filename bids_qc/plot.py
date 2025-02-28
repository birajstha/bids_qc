import pandas as pd
from multiprocessing import Pool
import os
from tqdm import tqdm
from colorama import Fore, Style, init
import nibabel as nib
from quickviz.plot_nii_overlay import plot_nii_overlay

def run(sub, ses, file_path_1, file_path_2, file_name, plots_dir, plot_path, logger):
    # # check if the above files exist
    # if not os.path.exists(file_path_1):
    #     print(Fore.RED + f"NO FILE: {file_name}" + Style.RESET_ALL)
    #     return

    # # # Check if the plot already exists
    # if os.path.exists(plot_path):
    #     print(Fore.YELLOW + f"Plot already exists: {file_name}" + Style.RESET_ALL)
    #     return

    # Check dimension and set volume index if 4D
    dim = len(nib.load(file_path_1).shape)
    volume_index = 0 if dim == 4 else None

    try:
        plot_nii_overlay(
            file_path_1,
            plot_path,
            cmap='bwr',
            title="",
            alpha=0.5,
            threshold="auto",
            background=file_path_2 if file_path_2 else None,
            volume=volume_index
        )
    except Exception as e:
        # print(Fore.RED + f"Error on {file_name}" + Style.RESET_ALL)
        # print(Fore.RED + f"Error: {e}" + Style.RESET_ALL)
        return f"Error on {file_name}: {e}"
    return f"Successfully plotted"