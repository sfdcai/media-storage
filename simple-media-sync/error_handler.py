"""
Centralized error handling and recovery system
"""

import logging
import time
from typing import Callable, Any
from functools import wraps


class ErrorHandler:
    """Centralized error handling with retry logic"""
    
    def __init__(self, logger):
        self.logger = logger
        self.retry_attempts = 3
        self.retry_delay = 5
    
    def retry_on_failure(self, max_attempts: int = 3, delay: int = 5):
        """Decorator for retry logic"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                last_exception = None
                
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                            time.sleep(delay)
                        else:
                            self.logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                
                raise last_exception
            return wrapper
        return decorator
    
    def handle_file_operation(self, operation: str, file_path: str, func: Callable) -> bool:
        """Handle file operations with error recovery"""
        try:
            return func()
        except PermissionError:
            self.logger.error(f"Permission denied for {operation}: {file_path}")
            return False
        except FileNotFoundError:
            self.logger.error(f"File not found for {operation}: {file_path}")
            return False
        except OSError as e:
            self.logger.error(f"OS error for {operation}: {file_path} - {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error for {operation}: {file_path} - {e}")
            return False
    
    def handle_network_operation(self, operation: str, func: Callable) -> bool:
        """Handle network operations with error recovery"""
        try:
            return func()
        except ConnectionError:
            self.logger.error(f"Connection error for {operation}")
            return False
        except TimeoutError:
            self.logger.error(f"Timeout error for {operation}")
            return False
        except Exception as e:
            self.logger.error(f"Network error for {operation}: {e}")
            return False
