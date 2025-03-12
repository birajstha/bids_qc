import pandas as pd
from multiprocessing import Pool
import os
from tqdm import tqdm
from colorama import Fore, Style, init
import nibabel as nib
from nilearn.plotting import plot_stat_map
import matplotlib.pyplot as plt
import numpy as np

from CPACqc.logging.log import logger

def plot_nii_overlay(in_nii, plot_loc, background=None, volume=None, cmap='viridis', title=None, alpha=0.8, threshold=20):
    im = nib.load(in_nii)
    if volume is not None:
        v = volume
        im = nib.Nifti1Image(im.get_fdata()[:,:,:,v], header=im.header, affine=im.affine)

    if threshold != 'auto':
        lb = np.percentile(np.sort(np.unique(im.get_fdata())), float(threshold))
    else:
        lb = threshold

    if background and background != 'None':
        bg = nib.load(background)
        plot_stat_map(im, bg_img=bg, output_file=plot_loc,
                      black_bg=True, threshold=lb, title=title, cmap=cmap, alpha=float(alpha))
    
    elif background == None or background == 'None':
        plot_stat_map(im, bg_img=None, output_file=plot_loc,
                      black_bg=True, threshold=lb, title=title, cmap=cmap, alpha=float(alpha))
                                                                                                        
    else:
        plot_stat_map(im, output_file=plot_loc,
                      black_bg=True, threshold=lb, title=title, cmap=cmap, alpha=float(alpha))


def run(sub, ses, file_path_1, file_path_2, file_name, plots_dir, plot_path):
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