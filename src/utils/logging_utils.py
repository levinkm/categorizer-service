import logging
from logging.handlers import RotatingFileHandler
import os
from src.utils.config_utils import config

def setup_logger(name: str) -> logging.Logger:
    """
    Set up and return a logger for the given name.
    
    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logging_conf = config.get("logging", {})
    
    # Set up basic configuration
    level = getattr(logging, logging_conf.get("level", "INFO"))
    log_format = logging_conf.get("format", '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    date_format = logging_conf.get("date_format", '%Y-%m-%d %H:%M:%S')

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create formatters
    formatter = logging.Formatter(log_format, date_format)

    # Set up console handler
    if logging_conf.get("console_output", True):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Set up file handler with rotation
    if logging_conf.get("file_output", False):
        log_file = logging_conf.get("file", "app.log")
        
        # Ensure that max_file_size is an integer
        max_file_size = int(logging_conf.get("max_file_size", 5 ))* 1024 * 1024  # Default 5MB
        backup_count = int(logging_conf.get("backup_count", 3))
        
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_file_size, 
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
