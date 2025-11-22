"""
Unit tests for the logger module.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import csv
import time

from tuner.config import TunerConfig
from tuner.logger import TunerLogger
from tuner.nt_interface import ShotData


class TestTunerLogger(unittest.TestCase):
    """Test TunerLogger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for logs
        self.temp_dir = tempfile.mkdtemp()
        
        self.config = TunerConfig()
        self.config.LOG_DIRECTORY = self.temp_dir
        
        self.logger = TunerLogger(self.config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.logger.close()
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test logger initialization."""
        self.assertIsNotNone(self.logger.csv_file)
        self.assertTrue(self.logger.csv_file.exists())
    
    def test_log_file_creation(self):
        """Test that log file is created with correct name."""
        log_file = self.logger.get_log_file_path()
        
        self.assertIsNotNone(log_file)
        self.assertTrue(log_file.exists())
        self.assertTrue(str(log_file).endswith('.csv'))
    
    def test_log_shot(self):
        """Test logging shot data."""
        shot_data = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        coefficient_values = {
            'kDragCoefficient': 0.003,
            'kLaunchHeight': 0.8,
        }
        
        self.logger.log_shot(
            coefficient_name='kDragCoefficient',
            coefficient_value=0.003,
            step_size=0.001,
            iteration=1,
            shot_data=shot_data,
            nt_connected=True,
            match_mode=False,
            tuner_status='Tuning',
            all_coefficient_values=coefficient_values
        )
        
        # Verify file was written
        self.logger.close()
        
        with open(self.logger.csv_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Should have header + 1 data row
            self.assertEqual(len(rows), 2)
            
            # Check data row has correct number of columns
            self.assertEqual(len(rows[1]), len(rows[0]))
    
    def test_log_event(self):
        """Test logging events."""
        self.logger.log_event('TEST', 'Test event message')
        
        self.logger.close()
        
        with open(self.logger.csv_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Should have header + event row
            self.assertGreaterEqual(len(rows), 2)
    
    def test_log_statistics(self):
        """Test logging statistics."""
        stats = {
            'coefficient_name': 'kDragCoefficient',
            'iterations': 10,
            'best_value': 0.0035,
            'hit_rate': 0.75,
        }
        
        self.logger.log_statistics(stats)
        
        self.logger.close()
        
        with open(self.logger.csv_file, 'r') as f:
            content = f.read()
            self.assertIn('STATISTICS', content)
    
    def test_context_manager(self):
        """Test context manager usage."""
        temp_dir = tempfile.mkdtemp()
        config = TunerConfig()
        config.LOG_DIRECTORY = temp_dir
        
        with TunerLogger(config) as logger:
            log_file = logger.get_log_file_path()
            self.assertTrue(log_file.exists())
        
        # File should be closed after context
        # Clean up
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
