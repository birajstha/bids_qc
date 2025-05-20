import pandas as pd
import os
from colorama import Fore, Style
import json
import shutil

from CPACqc.core.utils import (
    process_row, gen_filename, generate_plot_path, create_directory, get_file_info
)
from CPACqc.utils.multiprocessing.multiprocessing_utils import Multiprocess
from CPACqc.utils.report.pdf import Report
from CPACqc.core.config import Config
from CPACqc.utils.tabler.bids2table import Bids2TableDetails
from CPACqc.core.entity import Table
from CPACqc.utils.plotting.plot import Plot

class QCPipeline:
    def __init__(self, args):
        self.app_config = Config(
            bids_dir=args.bids_dir,
            qc_dir=args.qc_dir,
            subject_list=args.sub,
            overlay_csv=args.config,
            n_procs=args.n_procs
        )
        self.app_config.plots_dir = os.path.join(self.app_config.qc_dir, "plots")
        self.app_config.overlay_dir = os.path.join(self.app_config.qc_dir, "overlays")
        self.app_config.csv_dir = os.path.join(self.app_config.qc_dir, "csv")
        self.app_config.make_dirs()

        self.logger = self.app_config.logger
        self.bids_parser = Bids2TableDetails(
            base_dir=self.app_config.bids_dir,
            subjects=self.app_config.subject_list,
            workers=self.app_config.n_procs
        )
        self.my_table = Table(self.bids_parser.get_dataframe())
        self.nii_gz_files = self.my_table.processed_table
        self.overlay_df = pd.read_csv(self.app_config.overlay_csv).fillna(False)
        self.not_plotted = []

        self.cols_to_keep = ['sub', 'ses', 'file_path_1', 'file_path_2', 'file_name', 'plots_dir', 'plot_path', 'datatype', 'resource_name', 'space', 'scan']

    def run(self):
        sub_ses_list = self.nii_gz_files["sub_ses"].unique()
        for idx, sub_ses in enumerate(sub_ses_list, 1):
            print(Fore.YELLOW + f"Processing subject {idx}/{len(sub_ses_list)}: {sub_ses}" + Style.RESET_ALL)
            sub_df = self.nii_gz_files[self.nii_gz_files["sub_ses"] == sub_ses]
            self.process_subject(sub_ses, sub_df)
        self.cleanup_qc_dir()
        self.logger.info(f"QC pipeline completed for {len(sub_ses_list)} subjects.")

    def process_subject(self, sub_ses, sub_df):
        report = self.init_report(sub_ses)
        result_df = self.generate_results(sub_df, report)
        result_df = self.add_missing_rows(result_df, sub_df)
        result_df = self.add_additional_columns(result_df)
        result_df = self.remove_duplicates(result_df)
        self.save_results(result_df, sub_ses)
        self.run_plotting(result_df)
        self.generate_report(result_df, report)

    def init_report(self, sub_ses):
        return Report(
            qc_dir=self.app_config.qc_dir,
            sub_ses=sub_ses,
            overlay_df=self.overlay_df
        )

    def generate_results(self, sub_df, report):
        results = self.overlay_df.apply(
            lambda row: process_row(row, sub_df, self.app_config.overlay_dir, self.app_config.plots_dir, report),
            axis=1
        ).tolist()
        results = [item for sublist in results for item in sublist]
        return pd.DataFrame(results)

    def add_missing_rows(self, result_df, sub_df):
        if 'file_path_1' not in result_df.columns:
            result_df['file_path_1'] = None
        missing_rows = sub_df.loc[~sub_df['file_path'].isin(result_df['file_path_1'])].copy()
        if not missing_rows.empty:
            missing_rows['file_path_1'] = missing_rows['file_path']
            missing_rows['file_path_2'] = None
            missing_rows['file_name'] = missing_rows.apply(lambda row: gen_filename(res1_row=row), axis=1)
            missing_rows['plots_dir'] = self.app_config.plots_dir
            missing_rows['plot_path'] = missing_rows.apply(
                lambda row: generate_plot_path(create_directory(row['sub'], row['ses'], row['plots_dir']), row['file_name']),
                axis=1
            )
            cols = ['sub', 'ses', 'file_path_1', 'file_path_2', 'file_name', 'plots_dir', 'plot_path', 'datatype', 'resource_name', 'space', 'scan']
            if 'json' in missing_rows.columns:
                cols.append('json')
            missing_rows = missing_rows[cols].copy()
            result_df = pd.concat([result_df, missing_rows], ignore_index=True)
        return result_df

    def add_additional_columns(self, result_df):
        result_df['relative_path'] = result_df.apply(lambda row: os.path.relpath(row['plot_path'], self.app_config.qc_dir), axis=1)
        result_df['file_info'] = result_df.apply(lambda row: get_file_info(row['file_path_1']), axis=1)
        return result_df

    def save_results(self, result_df, sub_ses):
        result_df_csv_path = os.path.join(self.app_config.csv_dir, f"{sub_ses}_results.csv")
        result_df.to_csv(
            result_df_csv_path,
            mode='a' if os.path.exists(result_df_csv_path) else 'w',
            header=not os.path.exists(result_df_csv_path),
            index=False
        )

    def remove_duplicates(self, result_df):
        subset_cols = [
            "file_path_1", "file_path_2", "file_name", "plots_dir", "plot_path",
            "datatype", "resource_name", "space", "scan"
        ]
        if 'json' in result_df.columns:
            result_df['json'] = result_df['json'].apply(
                lambda x: json.dumps(x, sort_keys=True) if isinstance(x, dict) else (x if pd.isna(x) else str(x))
            )
            subset_cols.append("json")
        return result_df.drop_duplicates(subset=subset_cols, keep="first")

    def run_plotting(self, result_df):
        my_plots = [
            Plot(
                sub=row['sub'],
                ses=row['ses'],
                file_path_1=row['file_path_1'],
                file_path_2=row['file_path_2'],
                file_name=row['file_name'],
                plots_dir=row['plots_dir'],
                plot_path=row['plot_path']
            ) for _, row in result_df.iterrows()
        ]
        overlay_multiprocessor = Multiprocess(Plot.plot_overlay, my_plots, self.app_config.n_procs)
        self.not_plotted += overlay_multiprocessor.run()

    def generate_report(self, result_df, report):
        try:
            report.df = result_df
            report.generate_report()
            report.save_report()
            Report.destroy_instance()
        except Exception as e:
            print(Fore.RED + f"Error generating PDF: {e}" + Style.RESET_ALL)

    def cleanup_qc_dir(self):
        """
        Remove temporary QC directory or unnecessary files after processing.
        If using a temp QC dir, copy only report PDFs to the current directory before deleting.
        """
        dirs_to_remove = [
            self.app_config.plots_dir,
            self.app_config.overlay_dir,
            self.app_config.csv_dir
        ]
        for qc_dir in dirs_to_remove:
            if os.path.exists(qc_dir):
                print(Fore.YELLOW + f"Removing the QC output directory: {qc_dir}" + Style.RESET_ALL)
                shutil.rmtree(qc_dir)
            else:
                print(Fore.YELLOW + f"QC output directory does not exist: {qc_dir}" + Style.RESET_ALL)
        if '.temp_qc' in self.app_config.qc_dir:
            # Copy only PDF files from temp QC dir to current working directory
            for root, _, files in os.walk(self.app_config.qc_dir):
                for file in files:
                    if file.endswith('.pdf'):
                        src = os.path.join(root, file)
                        dst = os.path.join(os.getcwd(), file)
                        shutil.copy2(src, dst)
            shutil.rmtree(self.app_config.qc_dir)
