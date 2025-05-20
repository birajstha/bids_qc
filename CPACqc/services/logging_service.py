from abc import ABC, abstractmethod

class LoggerService(ABC):
    """
    Abstract class for logging adapters.
    """
    @abstractmethod
    def info(self, message: str):
        """
        Log an info message.
        """
        pass

    @abstractmethod
    def error(self, message: str):
        """
        Log an error message.
        """
        pass

    @abstractmethod
    def debug(self, message: str):
        """
        Log a debug message.
        """
        pass

    @abstractmethod
    def warning(self, message: str):
        """
        Log a warning message.
        """
        pass
    