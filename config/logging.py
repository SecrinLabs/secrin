"""
Centralized Logging Configuration for DevSecrin

This module provides a consistent logging setup across the entire application.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

from .env import Settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels in terminal output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to levelname for terminal output
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.RESET)
            record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        return super().format(record)


class DevSecrinLogger:
    """Centralized logger configuration for DevSecrin"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        log_file_path = Path(self.settings.LOG_FILE)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.settings.LOG_LEVEL))
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.settings.LOG_LEVEL))
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.settings.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        
        # Formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Apply formatters
        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(detailed_formatter)
        
        # Add handlers to root logger
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # Set specific log levels for noisy libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('chromadb').setLevel(logging.WARNING)
        
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific module"""
        return logging.getLogger(name)


# Global logger instance
_logger_instance: Optional[DevSecrinLogger] = None


def setup_logging(settings: Settings) -> DevSecrinLogger:
    """Setup global logging configuration"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = DevSecrinLogger(settings)
    return _logger_instance


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module"""
    if _logger_instance is None:
        # Initialize with default settings if not already done
        # Import here to avoid circular imports
        settings_obj = Settings()
        setup_logging(settings_obj)
    return _logger_instance.get_logger(name)


# Convenience functions for common logging patterns
def log_function_call(logger: logging.Logger, func_name: str, **kwargs):
    """Log function entry with parameters"""
    params = ', '.join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug(f"🔧 Calling {func_name}({params})")


def log_performance(logger: logging.Logger, operation: str, duration: float):
    """Log performance metrics"""
    logger.info(f"⏱️  {operation} took {duration:.2f} seconds")


def log_progress(logger: logging.Logger, current: int, total: int, operation: str):
    """Log progress for long-running operations"""
    percentage = (current / total) * 100 if total > 0 else 0
    logger.info(f"📊 {operation}: {current}/{total} ({percentage:.1f}%)")


def log_error_with_context(logger: logging.Logger, error: Exception, context: str):
    """Log error with additional context"""
    logger.error(f"❌ {context}: {type(error).__name__}: {str(error)}")


def log_success(logger: logging.Logger, message: str):
    """Log success message"""
    logger.info(f"✅ {message}")


def log_warning(logger: logging.Logger, message: str):
    """Log warning message"""
    logger.warning(f"⚠️ {message}")
