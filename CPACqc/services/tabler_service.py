from abc import ABC, abstractmethod
import pandas as pd

class TablerService(ABC):
    @abstractmethod
    def get_dataframe(self, base_dir: str, subjects: list, workers:int) -> pd.DataFrame:
        """
        Abstract method to convert a BIDS directory to a DataFrame.
        
        Parameters:
        - base_dir: str, path to the BIDS directory
        - subjects: list of str, subject IDs to include in the tabulation
        
        Returns:
        - df: pandas DataFrame, tabulated data
        """
        pass