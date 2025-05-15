from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import os
import pandas

from CPACqc.utils.logging.log import FileLogger

@dataclass
class Config:
    bids_dir: str
    qc_dir: Optional[str] = None
    subject_list: Optional[List[str]] = None
    n_procs: int = 8

    logger: FileLogger = field(init=False)
    overlay_csv: Optional[str] = None

    plots_dir: str = field(init=False)
    overlay_dir: str = field(init=False)
    csv_dir: str = field(init=False)

    def __post_init__(self):
        log_file = f"cpacqc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = FileLogger(name="CPACqc", filename=log_file)

        if not self.overlay_csv:
            self.overlay_csv = os.path.join(os.path.dirname(__file__), "..", "utils", "overlay", "overlay.csv")

        if not self.qc_dir:
            self.qc_dir = os.path.join(os.getcwd(), '.temp_qc')


    def make_dirs(self):
        """
        Create necessary directories for QC output.
        """
        os.makedirs(self.qc_dir, exist_ok=True)
        os.makedirs(self.plots_dir, exist_ok=True)
        os.makedirs(self.overlay_dir, exist_ok=True)
        os.makedirs(self.csv_dir, exist_ok=True)
