from CPACqc.utils.logging.log import FileLogger
from datetime import datetime
import os

log_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"cpacqc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logger = FileLogger(name="CPACqc", filename=log_file)