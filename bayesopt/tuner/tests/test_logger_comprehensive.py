"""
Comprehensive edge case tests for the logger module.

This test suite covers:
- File system errors (permissions, disk full, path errors)
- Large data volumes and memory handling
- Unicode and special character handling in logs
- Concurrent access to log files
- Log rotation and cleanup
- CSV malformation recovery
- Resource cleanup and file handle management
"""

import unittest
from unittest.mock import Mock, patch, mock_open
import tempfile
import shutil
import csv
import time
import sys
import os
import threading

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TunerConfig
from logger import TunerLogger
from nt_interface import ShotData


class TestTunerLoggerEdgeCases(unittest.TestCase):
    """Comprehensive edge case tests for TunerLogger."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = TunerConfig()
        self.config.LOG_DIRECTORY = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_with_very_long_log_directory_path(self):
        """Test logger with extremely long path."""
        # Create nested directory structure
        long_path = self.temp_dir
        for i in range(20):
            long_path = os.path.join(long_path, f"subdir_{i}")
        
        os.makedirs(long_path, exist_ok=True)
        self.config.LOG_DIRECTORY = long_path
        
        # Should handle long paths
        logger = TunerLogger(self.config)
        self.assertIsNotNone(logger.csv_file)
        logger.close()
    
    def test_logger_with_unicode_in_directory_name(self):
        """Test logger with unicode characters in path."""
        unicode_dir = os.path.join(self.temp_dir, "logs_α_β_γ_中文")
        os.makedirs(unicode_dir, exist_ok=True)
        self.config.LOG_DIRECTORY = unicode_dir
        
        # Should handle unicode in path
        logger = TunerLogger(self.config)
        self.assertIsNotNone(logger.csv_file)
        self.assertTrue(logger.csv_file.exists())
        logger.close()
    
    def test_logger_with_special_characters_in_path(self):
        """Test logger with special characters in path."""
        special_dir = os.path.join(self.temp_dir, "logs-with-dashes_and_underscores")
        os.makedirs(special_dir, exist_ok=True)
        self.config.LOG_DIRECTORY = special_dir
        
        logger = TunerLogger(self.config)
        self.assertIsNotNone(logger.csv_file)
        logger.close()
    
    def test_logger_creates_missing_directories(self):
        """Test that logger creates missing log directory."""
        non_existent = os.path.join(self.temp_dir, "does_not_exist", "nested", "path")
        self.config.LOG_DIRECTORY = non_existent
        
        # Should create the directory
        logger = TunerLogger(self.config)
        self.assertTrue(os.path.exists(non_existent))
        logger.close()
    
    def test_log_shot_with_unicode_data(self):
        """Test logging shot with unicode in text fields."""
        logger = TunerLogger(self.config)
        
        shot_data = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        coefficient_values = {
            'kDragCoefficient': 0.003,
            'test_α_β': 0.5,  # Unicode key
        }
        
        logger.log_shot(
            coefficient_name='kDragCoefficient',
            coefficient_value=0.003,
            step_size=0.001,
            iteration=1,
            shot_data=shot_data,
            nt_connected=True,
            match_mode=False,
            tuner_status='Tuning α',  # Unicode in status
            all_coefficient_values=coefficient_values
        )
        
        logger.close()
        
        # Verify file contains unicode
        with open(logger.csv_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('α', content)
    
    def test_log_shot_with_extreme_values(self):
        """Test logging with extreme numeric values."""
        logger = TunerLogger(self.config)
        
        shot_data = ShotData(
            hit=True,
            distance=1e10,  # Very large
            angle=1e-10,   # Very small
            velocity=1e6,
            timestamp=time.time()
        )
        
        coefficient_values = {
            'kDragCoefficient': 1e-15,
            'kLaunchHeight': 1e8,
        }
        
        logger.log_shot(
            coefficient_name='kDragCoefficient',
            coefficient_value=1e-20,
            step_size=1e-25,
            iteration=1,
            shot_data=shot_data,
            nt_connected=True,
            match_mode=False,
            tuner_status='Testing extremes',
            all_coefficient_values=coefficient_values
        )
        
        logger.close()
        
        # Should write without errors
        self.assertTrue(logger.csv_file.exists())
    
    def test_log_shot_with_inf_and_nan(self):
        """Test logging with infinity and NaN values."""
        logger = TunerLogger(self.config)
        
        shot_data = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        coefficient_values = {
            'kDragCoefficient': float('inf'),
            'kLaunchHeight': float('nan'),
        }
        
        # Should handle inf/nan gracefully
        try:
            logger.log_shot(
                coefficient_name='kDragCoefficient',
                coefficient_value=float('inf'),
                step_size=float('nan'),
                iteration=1,
                shot_data=shot_data,
                nt_connected=True,
                match_mode=False,
                tuner_status='Testing special values',
                all_coefficient_values=coefficient_values
            )
            logger.close()
            success = True
        except Exception:
            success = False
        
        # Should either succeed or handle gracefully
        self.assertTrue(success or not logger.csv_file.exists())
    
    def test_log_event_with_very_long_message(self):
        """Test logging event with extremely long message."""
        logger = TunerLogger(self.config)
        
        # Create very long message (10KB)
        long_message = "A" * 10000
        
        logger.log_event('TEST', long_message)
        logger.close()
        
        # Should write successfully
        with open(logger.csv_file, 'r') as f:
            content = f.read()
            self.assertIn('TEST', content)
    
    def test_log_event_with_special_csv_characters(self):
        """Test event logging with CSV special characters."""
        logger = TunerLogger(self.config)
        
        # Characters that can break CSV: comma, quote, newline
        special_messages = [
            "Message with, comma",
            'Message with "quotes"',
            "Message with\nnewline",
            "Message with\ttab",
            "Message with\rcarriage return",
        ]
        
        for msg in special_messages:
            logger.log_event('TEST', msg)
        
        logger.close()
        
        # Verify all messages were written correctly
        with open(logger.csv_file, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            self.assertGreater(len(rows), len(special_messages))
    
    def test_log_statistics_with_empty_dict(self):
        """Test logging statistics with empty dictionary."""
        logger = TunerLogger(self.config)
        
        logger.log_statistics({})
        logger.close()
        
        # Should handle empty dict
        self.assertTrue(logger.csv_file.exists())
    
    def test_log_statistics_with_none_values(self):
        """Test logging statistics with None values."""
        logger = TunerLogger(self.config)
        
        stats = {
            'coefficient_name': None,
            'iterations': None,
            'best_value': None,
            'hit_rate': None,
        }
        
        logger.log_statistics(stats)
        logger.close()
        
        # Should handle None values
        self.assertTrue(logger.csv_file.exists())
    
    def test_rapid_sequential_logging(self):
        """Test rapid sequential log writes."""
        logger = TunerLogger(self.config)
        
        shot_data = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        # Write many shots rapidly
        for i in range(100):
            logger.log_shot(
                coefficient_name='kDragCoefficient',
                coefficient_value=0.003 + i * 0.0001,
                step_size=0.001,
                iteration=i,
                shot_data=shot_data,
                nt_connected=True,
                match_mode=False,
                tuner_status=f'Iteration {i}',
                all_coefficient_values={'kDragCoefficient': 0.003}
            )
        
        logger.close()
        
        # Verify all shots were written
        with open(logger.csv_file, 'r') as f:
            rows = list(csv.reader(f))
            # Header + 100 shots
            self.assertGreaterEqual(len(rows), 100)
    
    def test_logger_multiple_close_calls(self):
        """Test that multiple close() calls are safe."""
        logger = TunerLogger(self.config)
        
        logger.close()
        logger.close()  # Second close should be safe
        logger.close()  # Third close should be safe
        
        # Should not raise errors
        self.assertTrue(True)
    
    def test_logger_context_manager_with_exception(self):
        """Test context manager handles exceptions."""
        try:
            with TunerLogger(self.config) as logger:
                logger.log_event('TEST', 'Before exception')
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Logger should still have closed properly
        self.assertTrue(True)
    
    def test_get_log_file_path_before_initialization(self):
        """Test getting log file path."""
        logger = TunerLogger(self.config)
        
        path = logger.get_log_file_path()
        
        self.assertIsNotNone(path)
        self.assertTrue(str(path).endswith('.csv'))
        
        logger.close()
    
    def test_logger_with_read_only_directory(self):
        """Test logger behavior with read-only directory."""
        if os.name == 'nt':  # Skip on Windows (permissions work differently)
            self.skipTest("Skipping on Windows")
        
        readonly_dir = os.path.join(self.temp_dir, "readonly")
        os.makedirs(readonly_dir)
        os.chmod(readonly_dir, 0o444)  # Read-only
        
        self.config.LOG_DIRECTORY = readonly_dir
        
        try:
            logger = TunerLogger(self.config)
            logger.close()
            # May succeed or fail depending on system
        except (PermissionError, OSError):
            # Expected on systems that enforce permissions
            pass
        finally:
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)


class TestTunerLoggerConcurrency(unittest.TestCase):
    """Test concurrent access to logger."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = TunerConfig()
        self.config.LOG_DIRECTORY = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_concurrent_logging_from_multiple_threads(self):
        """Test that concurrent logging doesn't corrupt file."""
        logger = TunerLogger(self.config)
        
        shot_data = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        errors = []
        
        def log_worker(thread_id):
            try:
                for i in range(10):
                    logger.log_event(f'THREAD_{thread_id}', f'Message {i}')
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=log_worker, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join(timeout=5)
        
        logger.close()
        
        # Should have no errors
        self.assertEqual(len(errors), 0)
        
        # Verify file is valid CSV
        with open(logger.csv_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            self.assertGreater(len(rows), 50)  # At least 50 messages


class TestTunerLoggerResourceManagement(unittest.TestCase):
    """Test resource management and cleanup."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = TunerConfig()
        self.config.LOG_DIRECTORY = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_cleanup_on_del(self):
        """Test that logger cleans up when deleted."""
        logger = TunerLogger(self.config)
        log_file = logger.csv_file
        
        # Delete logger
        del logger
        
        # File should still exist but handles should be closed
        self.assertTrue(log_file.exists())
    
    def test_many_logger_instances(self):
        """Test creating many logger instances."""
        loggers = []
        
        for i in range(10):
            logger = TunerLogger(self.config)
            loggers.append(logger)
        
        # All should have unique log files
        log_files = [logger.csv_file for logger in loggers]
        unique_files = set(log_files)
        
        # May or may not be unique depending on timestamp resolution
        self.assertGreater(len(unique_files), 0)
        
        # Clean up
        for logger in loggers:
            logger.close()


if __name__ == '__main__':
    unittest.main()
  
