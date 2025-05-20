# from CPACqc.utils.tabler.custom_bids2table._b2t import bids2table
# import pandas as pd
# from CPACqc.services.tabler_service import TablerService

# class Bids2TableDetails(TablerService):
    
#     def __init__(self, base_dir, subjects=None, workers=8):
#         """
#         Initialize the Bids2TableDetails class.

#         Parameters:
#         - base_dir (str): The base directory for BIDS data.
#         - subjects (list): List of subjects to process. If None, all subjects will be processed.
#         """
#         self.base_dir = base_dir
#         self.subjects = subjects if subjects else []
#         self.workers = workers

#     def _parse_bids(self):
#         """
#         Parse the BIDS directory and return a DataFrame with the results.

#         Returns:
#         - pd.DataFrame: DataFrame containing the parsed BIDS data.
#         """
#         df = bids2table(self.base_dir, subject=self.subjects, workers = self.workers).flat
#         return df

#     def get_dataframe(self):
#         """
#         Convert the parsed BIDS data to a DataFrame.

#         Returns:
#         - pd.DataFrame: DataFrame containing the parsed BIDS data.
#         """
#         df = self._parse_bids()
#         return df



import bids2table as b2t
import pandas as pd
from CPACqc.services.tabler_service import TablerService

class Bids2TableDetails(TablerService):
    
    def __init__(self, base_dir, subjects=None, workers=8):
        """
        Initialize the Bids2TableDetails class.

        Parameters:
        - base_dir (str): The base directory for BIDS data.
        - subjects (list): List of subjects to process. If None, all subjects will be processed.
        """
        self.base_dir = base_dir
        self.subjects = subjects if subjects else []
        self.workers = workers
        self.arrow = self._parse_bids()

    def _parse_bids(self):
        return b2t.index_dataset(root=self.base_dir, include_subjects=self.subjects, show_progress=True)

    def get_dataframe(self):
        """
        Convert the parsed BIDS data to a DataFrame.

        Returns:
        - pd.DataFrame: DataFrame containing the parsed BIDS data.
        """
        df = self.arrow.to_pandas(types_mapper=pd.ArrowDtype)
        return df



    
    
