
from abc import ABC, abstractmethod

class ReportGeneratorService(ABC):
    """
    Abstract base class for report generation services.
    """

    @abstractmethod
    def generate_report(self, entity, config):
        """
        Generate a report based on the provided data.

        :param data: The data to be included in the report.
        :return: The generated report.
        """
        pass

    @abstractmethod
    def save_report(self, report, file_path):
        """
        Save the generated report to a file.

        :param report: The report to be saved.
        :param file_path: The path where the report will be saved.
        """
        pass