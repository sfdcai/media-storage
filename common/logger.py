#!/usr/bin/env python3
"""
Centralized Logging Management
Provides consistent logging configuration across all modules
"""

import os
import logging
import logging.handlers
from typing import Optional
from pathlib import Path
from common.config import config_manager

class LoggerManager:
    """Centralized logging manager"""
    
    _loggers: dict = {}
    _initialized: bool = False
    
    @classmethod
    def initialize(cls):
        """Initialize logging system"""
        if cls._initialized:
            return
        
        log_config = config_manager.get_logging_config()
        
        # Create log directory
        os.makedirs(log_config.log_dir, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_config.level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(log_config.format)
        
        # File handler with rotation
        log_file_path = os.path.join(log_config.log_dir, log_config.log_file)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=log_config.max_file_size_mb * 1024 * 1024,
            backupCount=log_config.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, log_config.level.upper()))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, log_config.level.upper()))
        
        # Add handlers to root logger
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        cls._initialized = True
        logging.info("Logging system initialized")
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger instance"""
        if not cls._initialized:
            cls.initialize()
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def set_level(cls, level: str):
        """Set logging level for all loggers"""
        log_level = getattr(logging, level.upper())
        
        # Update root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Update all handlers
        for handler in root_logger.handlers:
            handler.setLevel(log_level)
        
        # Update all existing loggers
        for logger in cls._loggers.values():
            logger.setLevel(log_level)
    
    @classmethod
    def add_file_handler(cls, logger_name: str, filename: str, level: Optional[str] = None):
        """Add a specific file handler to a logger"""
        logger = cls.get_logger(logger_name)
        
        log_config = config_manager.get_logging_config()
        log_file_path = os.path.join(log_config.log_dir, filename)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=log_config.max_file_size_mb * 1024 * 1024,
            backupCount=log_config.backup_count,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(log_config.format)
        file_handler.setFormatter(formatter)
        
        if level:
            file_handler.setLevel(getattr(logging, level.upper()))
        
        logger.addHandler(file_handler)
        return file_handler

def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger"""
    return LoggerManager.get_logger(name)

def setup_module_logger(module_name: str) -> logging.Logger:
    """Setup logger for a specific module with its own log file"""
    logger = get_logger(module_name)
    
    # Add module-specific log file
    log_filename = f"{module_name}.log"
    LoggerManager.add_file_handler(module_name, log_filename)
    
    return logger
