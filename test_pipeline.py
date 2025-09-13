#!/usr/bin/env python3
"""
Pipeline Testing and Validation Script
Tests individual components and validates the pipeline setup
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict
from common import config_manager, db_manager, setup_module_logger, auth_manager

# Setup module-specific logger
logger = setup_module_logger(__name__)

class PipelineTester:
    """Tests and validates pipeline components"""
    
    def __init__(self):
        self.test_dir = None
        self.original_config = None
    
    def setup_test_environment(self):
        """Setup a test environment with temporary directories"""
        logger.info("Setting up test environment...")
        
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp(prefix="media_pipeline_test_")
        logger.info(f"Test directory: {self.test_dir}")
        
        # Create test subdirectories
        test_dirs = [
            "incoming", "backup", "compress", "delete_pending", "processed", "logs"
        ]
        for dir_name in test_dirs:
            os.makedirs(os.path.join(self.test_dir, dir_name), exist_ok=True)
        
        # Create test database
        test_db_path = os.path.join(self.test_dir, "test_media.db")
        os.environ['DB_FILE'] = test_db_path
        
        logger.info("✅ Test environment setup complete")
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            logger.info("🧹 Test environment cleaned up")
    
    def test_database_operations(self) -> bool:
        """Test database operations"""
        logger.info("Testing database operations...")
        
        try:
            # Initialize database
            db_manager.init_database()
            logger.info("✅ Database initialization successful")
            
            # Test adding a record
            test_record = db_manager.add_media_record(
                filename="test_image.jpg",
                icloud_id="test_123",
                created_date="2024-01-01T00:00:00",
                local_path="/test/path/test_image.jpg",
                status="downloaded"
            )
            
            if test_record:
                logger.info("✅ Database record creation successful")
            else:
                logger.warning("⚠️ Database record creation returned False (may already exist)")
            
            # Test getting pipeline stats
            stats = db_manager.get_pipeline_stats()
            logger.info(f"✅ Database stats retrieval successful: {stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database test failed: {e}")
            return False
    
    def test_configuration_management(self) -> bool:
        """Test configuration management"""
        logger.info("Testing configuration management...")
        
        try:
            # Test configuration loading
            db_config = config_manager.get_database_config()
            logger.info(f"✅ Database config loaded: {db_config.file_path}")
            
            icloud_config = config_manager.get_icloud_config()
            logger.info(f"✅ iCloud config loaded: {icloud_config.username}")
            
            syncthing_config = config_manager.get_syncthing_config()
            logger.info(f"✅ Syncthing config loaded: {syncthing_config.base_url}")
            
            # Test configuration validation
            validation_result = config_manager.validate_config()
            logger.info(f"✅ Configuration validation: {validation_result}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration test failed: {e}")
            return False
    
    def test_logging_system(self) -> bool:
        """Test logging system"""
        logger.info("Testing logging system...")
        
        try:
            # Test different log levels
            logger.debug("This is a debug message")
            logger.info("This is an info message")
            logger.warning("This is a warning message")
            logger.error("This is an error message")
            
            logger.info("✅ Logging system test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Logging test failed: {e}")
            return False
    
    def test_authentication_connections(self) -> bool:
        """Test authentication connections (without credentials)"""
        logger.info("Testing authentication connections...")
        
        try:
            # Test connection validation (will fail without credentials, but should not crash)
            connections = auth_manager.validate_all_connections()
            logger.info(f"✅ Connection validation completed: {connections}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication test failed: {e}")
            return False
    
    def test_file_operations(self) -> bool:
        """Test file operations"""
        logger.info("Testing file operations...")
        
        try:
            if not self.test_dir:
                logger.error("Test directory not set up")
                return False
            
            # Create a test file
            test_file_path = os.path.join(self.test_dir, "incoming", "test_file.txt")
            with open(test_file_path, 'w') as f:
                f.write("Test content")
            
            # Verify file exists
            if os.path.exists(test_file_path):
                logger.info("✅ File creation test successful")
            else:
                logger.error("❌ File creation test failed")
                return False
            
            # Test file size
            file_size = os.path.getsize(test_file_path)
            logger.info(f"✅ File size test successful: {file_size} bytes")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ File operations test failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests"""
        logger.info("🧪 Starting comprehensive pipeline tests...")
        
        results = {}
        
        # Setup test environment
        self.setup_test_environment()
        
        try:
            # Run individual tests
            results['database'] = self.test_database_operations()
            results['configuration'] = self.test_configuration_management()
            results['logging'] = self.test_logging_system()
            results['authentication'] = self.test_authentication_connections()
            results['file_operations'] = self.test_file_operations()
            
            # Calculate overall success
            overall_success = all(results.values())
            
            # Log results
            logger.info("📊 Test Results Summary:")
            for test_name, success in results.items():
                status = "✅ PASS" if success else "❌ FAIL"
                logger.info(f"  {test_name}: {status}")
            
            logger.info(f"Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
            
            return results
            
        finally:
            # Always cleanup
            self.cleanup_test_environment()

def main():
    """Main test runner"""
    logger.info("🚀 Starting Media Pipeline Test Suite")
    
    tester = PipelineTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    overall_success = all(results.values())
    exit_code = 0 if overall_success else 1
    
    logger.info(f"Test suite completed with exit code: {exit_code}")
    return exit_code

if __name__ == "__main__":
    exit(main())
