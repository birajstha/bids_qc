import pandas as pd
from multiprocessing import Pool
import os
from tqdm import tqdm
from colorama import Fore, Style, init
import nibabel as nib
from nilearn.plotting import plot_stat_map
import matplotlib.pyplot as plt
import numpy as np

from CPACqc.utils.plotting.nii_plotter import plot_nii_overlay


def run(sub, ses, file_path_1, file_path_2, file_name, plots_dir, plot_path):
    dim = len(nib.load(file_path_1).shape)
    volume_index = 0 if dim == 4 else None

    try:
        plot_nii_overlay(
            file_path_1,
            plot_path,
            background=file_path_2 if file_path_2 else None,
            volume=volume_index,
            cmap='bwr',
            title="",
            alpha=0.5,
            threshold="auto"
        )
    except Exception as e:
        # print(Fore.RED + f"Error on {file_name}" + Style.RESET_ALL)
        # print(Fore.RED + f"Error: {e}" + Style.RESET_ALL)
        return f"Error on {file_name}: {e}"
    return f"Successfully plotted"