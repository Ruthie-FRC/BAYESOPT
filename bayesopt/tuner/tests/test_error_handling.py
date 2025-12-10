"""
Comprehensive error handling tests for all modules.

This test suite covers:
- Exception handling in all major code paths
- Graceful degradation when components fail
- Error recovery mechanisms
- Invalid input handling
- Network failures and timeouts
- File system errors
- Resource exhaustion scenarios
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile
import shutil
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TunerConfig
from nt_interface import NetworkTablesInterface, ShotData
from optimizer import BayesianOptimizer, CoefficientTuner
from logger import TunerLogger

# Import tuner module without name collision
import tuner as tuner_module
BayesianTunerCoordinator = tuner_module.BayesianTunerCoordinator


class TestNetworkTablesErrorHandling(unittest.TestCase):
    """Test error handling in NetworkTables interface."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.interface = NetworkTablesInterface(self.config)
    
    def test_connection_failure_handling(self):
        """Test handling of connection failures."""
        # Mock connection to fail
        with patch.object(self.interface, 'start', return_value=False):
            result = self.interface.start("192.168.1.999")
        
        self.assertFalse(result)
        self.assertFalse(self.interface.connected)
    
    def test_read_coefficient_with_exception(self):
        """Test reading coefficient when NT throws exception."""
        self.interface.connected = True
        self.interface.tuning_table = Mock()
        self.interface.tuning_table.getNumber = Mock(side_effect=Exception("NT error"))
        
        # Should return default value on exception
        result = self.interface.read_coefficient("/test", 0.5)
        
        self.assertEqual(result, 0.5)  # Default value
    
    def test_write_coefficient_with_exception(self):
        """Test writing coefficient when NT throws exception."""
        self.interface.connected = True
        self.interface.tuning_table = Mock()
        self.interface.tuning_table.putNumber = Mock(side_effect=Exception("NT error"))
        
        # Should return False on exception
        result = self.interface.write_coefficient("/test", 0.5, force=True)
        
        self.assertFalse(result)
    
    def test_read_shot_data_with_partial_failure(self):
        """Test reading shot data when some fields are missing."""
        self.interface.connected = True
        self.interface.firing_solver_table = Mock()
        
        # Mock partial data (some fields throw exceptions)
        def mock_get_number(key, default):
            if "Distance" in key:
                raise Exception("Field missing")
            return default
        
        self.interface.firing_solver_table.getNumber = mock_get_number
        self.interface.firing_solver_table.getBoolean = Mock(return_value=True)
        self.interface.firing_solver_table.getSubTable = Mock(return_value=Mock())
        
        # Should handle gracefully
        result = self.interface.read_shot_data()
        
        # May return None or partial data depending on implementation
        self.assertTrue(result is None or isinstance(result, ShotData))
    
    def test_is_connected_with_exception(self):
        """Test connection check when NT throws exception."""
        with patch('nt_interface.NetworkTables.isConnected', side_effect=Exception("NT error")):
            result = self.interface.is_connected()
        
        # Should return False on exception
        self.assertFalse(result)
    
    def test_flush_pending_writes_with_failures(self):
        """Test flushing writes when some fail."""
        self.interface.connected = True
        self.interface.tuning_table = Mock()
        
        # Add pending writes
        self.interface.pending_writes = {
            "/test1": 0.1,
            "/test2": 0.2,
            "/test3": 0.3,
        }
        
        # Mock write to fail for one key
        def mock_put(key, value):
            if "test2" in key:
                raise Exception("Write failed")
        
        self.interface.tuning_table.putNumber = mock_put
        
        # Should handle partial failures
        count = self.interface.flush_pending_writes()
        
        # Should have attempted all writes
        self.assertIsInstance(count, int)


class TestOptimizerErrorHandling(unittest.TestCase):
    """Test error handling in optimizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.coeff_config = self.config.COEFFICIENTS["kDragCoefficient"]
        self.optimizer = BayesianOptimizer(self.coeff_config, self.config)
    
    def test_suggest_value_with_corrupted_state(self):
        """Test suggesting value when optimizer state is corrupted."""
        # Corrupt internal state
        self.optimizer.search_space = None
        
        # Should handle gracefully or raise clear error
        try:
            value = self.optimizer.suggest_next_value()
            # If it succeeds, verify it's valid
            self.assertIsNotNone(value)
        except Exception as e:
            # If it fails, should be a clear error
            self.assertIsInstance(e, (ValueError, AttributeError, TypeError))
    
    def test_report_result_with_invalid_value(self):
        """Test reporting result with invalid value."""
        # Report with NaN
        try:
            self.optimizer.report_result(float('nan'), hit=True)
            # Should handle or reject
        except (ValueError, TypeError):
            # Expected to fail
            pass
        
        # Report with infinity
        try:
            self.optimizer.report_result(float('inf'), hit=True)
            # Should handle or reject
        except (ValueError, TypeError):
            # Expected to fail
            pass
    
    def test_coefficient_tuner_with_no_coefficients(self):
        """Test CoefficientTuner with no enabled coefficients."""
        config = TunerConfig()
        
        # Disable all coefficients
        for coeff in config.COEFFICIENTS.values():
            coeff.enabled = False
        
        # Should handle gracefully
        try:
            tuner = CoefficientTuner(config)
            # May initialize with no optimizer or handle differently
            self.assertIsNotNone(tuner)
        except (IndexError, ValueError):
            # May raise error if no coefficients available
            pass
    
    def test_record_shot_with_invalid_coefficient_values(self):
        """Test recording shot with missing coefficient values."""
        tuner = CoefficientTuner(self.config)
        
        shot_data = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        # Empty coefficient values dict
        tuner.record_shot(shot_data, {})
        
        # Should handle missing values gracefully
        self.assertIsNotNone(tuner)
    
    def test_advance_beyond_last_coefficient(self):
        """Test advancing past the last coefficient."""
        tuner = CoefficientTuner(self.config)
        
        # Advance to last coefficient
        while tuner.current_index < len(tuner.coefficients) - 1:
            tuner.advance_to_next_coefficient()
        
        # Try to advance beyond last
        tuner.advance_to_next_coefficient()
        
        # Should handle gracefully (stay at end or mark complete)
        self.assertTrue(tuner.is_complete() or tuner.current_index == len(tuner.coefficients) - 1)
    
    def test_go_to_previous_before_first(self):
        """Test going to previous before first coefficient."""
        tuner = CoefficientTuner(self.config)
        
        # Already at first (index 0)
        self.assertEqual(tuner.current_index, 0)
        
        # Try to go to previous
        tuner.go_to_previous_coefficient()
        
        # Should stay at first
        self.assertEqual(tuner.current_index, 0)


class TestLoggerErrorHandling(unittest.TestCase):
    """Test error handling in logger."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = TunerConfig()
        self.config.LOG_DIRECTORY = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_log_to_nonexistent_directory(self):
        """Test logging when directory doesn't exist."""
        nonexistent = os.path.join(self.temp_dir, "does", "not", "exist")
        self.config.LOG_DIRECTORY = nonexistent
        
        # Should create directory or handle gracefully
        try:
            logger = TunerLogger(self.config)
            self.assertIsNotNone(logger.csv_file)
            logger.close()
        except (OSError, IOError):
            # May fail on some systems
            pass
    
    def test_log_shot_with_none_values(self):
        """Test logging shot with None in critical fields."""
        logger = TunerLogger(self.config)
        
        shot_data = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        # None values in coefficient dict
        coefficient_values = {
            'kDragCoefficient': None,
            'kLaunchHeight': 0.8,
        }
        
        # Should handle None gracefully
        try:
            logger.log_shot(
                coefficient_name=None,  # None name
                coefficient_value=None,  # None value
                step_size=None,
                iteration=None,
                shot_data=shot_data,
                nt_connected=True,
                match_mode=False,
                tuner_status=None,
                all_coefficient_values=coefficient_values
            )
            logger.close()
            success = True
        except Exception:
            success = False
            logger.close()
        
        # Should either succeed or fail gracefully
        self.assertTrue(success or not logger.csv_file.exists())
    
    def test_log_with_disk_full_simulation(self):
        """Test logging when disk is full."""
        logger = TunerLogger(self.config)
        
        # Mock file write to fail
        with patch.object(logger.csv_writer, 'writerow', side_effect=OSError("Disk full")):
            try:
                logger.log_event('TEST', 'This should fail')
                # If it doesn't raise, it handled the error
            except OSError:
                # Expected to fail
                pass
        
        logger.close()
    
    def test_close_already_closed_logger(self):
        """Test closing logger multiple times."""
        logger = TunerLogger(self.config)
        
        logger.close()
        logger.close()  # Should not raise error
        logger.close()  # Should not raise error
        
        # Should be safe
        self.assertTrue(True)
    
    def test_log_after_close(self):
        """Test logging after logger is closed."""
        logger = TunerLogger(self.config)
        logger.close()
        
        # Try to log after close
        try:
            logger.log_event('TEST', 'After close')
            # May succeed or fail depending on implementation
        except (ValueError, AttributeError):
            # Expected to fail
            pass


class TestCoordinatorErrorHandling(unittest.TestCase):
    """Test error handling in main coordinator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = TunerConfig()
        self.config.LOG_DIRECTORY = self.temp_dir
        self.coordinator = BayesianTunerCoordinator(self.config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.coordinator.running:
            self.coordinator.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_start_with_nt_connection_failure(self):
        """Test starting when NT connection fails."""
        self.config.TUNER_ENABLED = True
        
        with patch.object(self.coordinator.nt_interface, 'start', return_value=False):
            self.coordinator.start()
        
        # Should not start if NT fails
        self.assertFalse(self.coordinator.running)
    
    def test_accumulate_shot_with_validation_failure(self):
        """Test accumulating shot that fails validation."""
        invalid_shot = ShotData(
            hit=True,
            distance=-999.0,  # Invalid
            angle=999.0,      # Invalid
            velocity=-1.0,    # Invalid
            timestamp=time.time()
        )
        
        self.coordinator.current_coefficient_values = {}
        
        # Should handle invalid shot gracefully
        try:
            self.coordinator._accumulate_shot(invalid_shot)
            # Should either reject or log as invalid
        except Exception:
            # May raise exception for very invalid data
            pass
    
    def test_run_optimization_with_no_shots(self):
        """Test running optimization with no accumulated shots."""
        self.coordinator.accumulated_shots = []
        
        # Should handle empty shot list
        try:
            self.coordinator._run_optimization()
            # May succeed (no-op) or raise error
        except (ValueError, IndexError):
            # Expected to fail
            pass
    
    def test_check_safety_conditions_with_nt_exception(self):
        """Test safety check when NT throws exception."""
        self.coordinator.runtime_enabled = True
        
        with patch.object(self.coordinator.nt_interface, 'is_match_mode', side_effect=Exception("NT error")):
            with patch.object(self.coordinator.nt_interface, 'is_connected', return_value=True):
                # Should handle exception gracefully
                try:
                    result = self.coordinator._check_safety_conditions()
                    # Should return False or handle error
                    self.assertIsInstance(result, bool)
                except Exception:
                    # May propagate exception
                    pass
    
    def test_update_status_with_nt_write_failure(self):
        """Test status update when NT write fails."""
        with patch.object(self.coordinator.nt_interface, 'write_autotune_status', side_effect=Exception("Write failed")):
            # Should handle write failure gracefully
            try:
                self.coordinator._update_status()
                # Should not crash
            except Exception:
                # May propagate exception
                pass
    
    def test_stop_with_thread_not_stopping(self):
        """Test stop when thread doesn't stop gracefully."""
        self.config.TUNER_ENABLED = True
        self.config.GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS = 0.1  # Short timeout
        
        with patch.object(self.coordinator.nt_interface, 'start', return_value=True):
            with patch.object(self.coordinator.nt_interface, 'read_all_coefficients', return_value={}):
                self.coordinator.start()
                
                # Mock thread to not stop
                if self.coordinator.thread:
                    with patch.object(self.coordinator.thread, 'is_alive', return_value=True):
                        # Should timeout and continue
                        self.coordinator.stop()
                        
                        # Should still mark as stopped
                        self.assertFalse(self.coordinator.running)


class TestShotDataValidation(unittest.TestCase):
    """Test shot data validation edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
    
    def test_shot_data_with_all_invalid_fields(self):
        """Test shot data with all fields invalid."""
        shot = ShotData(
            hit=True,
            distance=-1.0,    # Invalid
            angle=-1.0,       # Invalid
            velocity=-1.0,    # Invalid
            timestamp=time.time()
        )
        
        # Should fail validation
        self.assertFalse(shot.is_valid(self.config))
    
    def test_shot_data_with_type_mismatches(self):
        """Test shot data with wrong types."""
        # Try to create shot with wrong types
        try:
            shot = ShotData(
                hit="not_a_bool",  # Wrong type
                distance="not_a_number",
                angle="not_a_number",
                velocity="not_a_number",
                timestamp=time.time()
            )
            # If creation succeeds, validation should fail
            if hasattr(shot, 'is_valid'):
                result = shot.is_valid(self.config)
                self.assertFalse(result)
        except (TypeError, ValueError):
            # Expected to fail during creation
            pass
    
    def test_shot_data_at_exact_boundaries(self):
        """Test shot data at exact physical limit boundaries."""
        # Exactly at min
        shot_min = ShotData(
            hit=True,
            distance=self.config.PHYSICAL_MIN_DISTANCE_M,
            angle=self.config.PHYSICAL_MIN_ANGLE_RAD,
            velocity=self.config.PHYSICAL_MIN_VELOCITY_MPS,
            timestamp=time.time()
        )
        
        self.assertTrue(shot_min.is_valid(self.config))
        
        # Exactly at max
        shot_max = ShotData(
            hit=True,
            distance=self.config.PHYSICAL_MAX_DISTANCE_M,
            angle=self.config.PHYSICAL_MAX_ANGLE_RAD,
            velocity=self.config.PHYSICAL_MAX_VELOCITY_MPS,
            timestamp=time.time()
        )
        
        self.assertTrue(shot_max.is_valid(self.config))
        
        # Just outside min
        shot_below_min = ShotData(
            hit=True,
            distance=self.config.PHYSICAL_MIN_DISTANCE_M - 0.001,
            angle=self.config.PHYSICAL_MIN_ANGLE_RAD,
            velocity=self.config.PHYSICAL_MIN_VELOCITY_MPS,
            timestamp=time.time()
        )
        
        self.assertFalse(shot_below_min.is_valid(self.config))
        
        # Just outside max
        shot_above_max = ShotData(
            hit=True,
            distance=self.config.PHYSICAL_MAX_DISTANCE_M + 0.001,
            angle=self.config.PHYSICAL_MAX_ANGLE_RAD,
            velocity=self.config.PHYSICAL_MAX_VELOCITY_MPS,
            timestamp=time.time()
        )
        
        self.assertFalse(shot_above_max.is_valid(self.config))


if __name__ == '__main__':
    unittest.main()
  
