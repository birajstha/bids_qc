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
from CPACqc.services.plotting_service import PlottingService

class Plot(PlottingService):
    def __init__(self, sub, ses, file_path_1, file_path_2, file_name, plots_dir, plot_path):
        self.sub = sub
        self.ses = ses
        self.file_path_1 = file_path_1
        self.file_path_2 = file_path_2
        self.file_name = file_name
        self.plots_dir = plots_dir
        self.plot_path = plot_path
        self.dim = len(nib.load(file_path_1).shape)
        self.volume_index = 0 if self.dim == 4 else None
        
    def plot_overlay(self):
        
        try:
            plot_nii_overlay(
                self.file_path_1,
                self.plot_path,
                background=self.file_path_2 if self.file_path_2 else None,
                volume=self.volume_index,
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

    def __repr__(self):
        return f"{self.file_name}"