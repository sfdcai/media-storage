#!/usr/bin/env python3
"""
Common modules package
Provides shared functionality for the media pipeline
"""

from .config import config_manager
from .logger import get_logger, setup_module_logger, LoggerManager
from .database import db_manager, DatabaseManager
from .auth import auth_manager, AuthenticationManager

__all__ = [
    'config_manager',
    'get_logger',
    'setup_module_logger', 
    'LoggerManager',
    'db_manager',
    'DatabaseManager',
    'auth_manager',
    'AuthenticationManager'
]
