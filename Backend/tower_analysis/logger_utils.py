import logging
import os
from datetime import datetime

def setup_logger(log_dir="logs", log_file=None, level=logging.INFO):
    """
    Setup a logger that writes both to file and console.

    Parameters:
        log_dir (str): Directory to store log files.
        log_file (str or None): Filename for the log. If None, auto-generate based on timestamp.
        level (int): Logging level (e.g., logging.INFO or logging.DEBUG)

    Returns:
        logging.Logger: Configured logger instance.
    """
    os.makedirs(log_dir, exist_ok=True)

    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"log_{timestamp}.log"
    elif not log_file.endswith(".log"):
        log_file += ".log"

    log_path = os.path.join(log_dir, log_file)

    # Avoid duplicate handlers if re-run
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(level)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

        # File handler
        file_handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Stream handler (console)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        logger.info(f"Logger initialized: {log_path}")
        logger.info(f"Current working directory: {os.getcwd()}")

    return logger
