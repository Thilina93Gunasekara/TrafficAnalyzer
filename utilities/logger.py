# utilities/logger.py
# Centralized logging utilities for the application

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

from config.settings import LoggingConfig


def setup_logging():
    """
    Setup centralized logging configuration for the entire application
    """
    try:
        # Create logs directory if it doesn't exist
        log_dir = Path(LoggingConfig.LOG_FILE).parent
        log_dir.mkdir(exist_ok=True)

        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, LoggingConfig.LOG_LEVEL))

        # Remove existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create formatters
        detailed_formatter = logging.Formatter(LoggingConfig.LOG_FORMAT)
        console_formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            LoggingConfig.LOG_FILE,
            maxBytes=LoggingConfig.MAX_LOG_SIZE,
            backupCount=LoggingConfig.BACKUP_COUNT
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)

        # Add handlers to root logger
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # Log successful setup
        logger = logging.getLogger(__name__)
        logger.info("Logging system initialized successfully")

    except Exception as e:
        print(f"Error setting up logging: {e}")
        # Fallback to basic configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module

    Args:
        name: Usually __name__ from the calling module

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)