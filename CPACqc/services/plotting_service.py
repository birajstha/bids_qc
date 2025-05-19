from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class PlottingService(ABC):

    @abstractmethod
    def plot_overlay(self, sub, ses, file_path_1, file_path_2, file_name, plots_dir, plot_path):
        """
        Abstract method to plot data.
        
        Parameters:
        - sub: str, subject ID
        - ses: str, session ID
        - file_path_1: str, path to the first file
        - file_path_2: Optional[str], path to the second file (if applicable)
        - file_name: str, name of the output plot file
        - plots_dir: str, directory where plots will be saved
        - plot_path: str, full path for the output plot
        
        Returns:
        - None
        """
        pass