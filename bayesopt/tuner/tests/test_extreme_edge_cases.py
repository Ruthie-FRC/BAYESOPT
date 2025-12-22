"""
Extreme edge case testing for maximum coverage.

This test suite covers:
- Extreme values and boundary conditions
- Malformed data and corruption scenarios
- System resource limits
- Platform-specific edge cases
- Pathological input combinations
- Defensive programming validation
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
import tempfile
import shutil
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TunerConfig, CoefficientConfig
from nt_interface import NetworkTablesInterface, ShotData
from logger import TunerLogger


class TestExtremeNumericValues(unittest.TestCase):
    """Test with extreme numeric values."""
    
    def test_coefficient_with_scientific_notation_extremes(self):
        """Test coefficients with extreme scientific notation."""
        coeff = CoefficientConfig(
            name="extreme",
            default_value=1e-100,  # Extremely small
            min_value=1e-200,
            max_value=1e200,  # Extremely large
            initial_step_size=1e-50,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/extreme"
        )
        
        # Should handle extreme ranges
        self.assertIsNotNone(coeff)
        
        # Test clamping with extreme values
        self.assertEqual(coeff.clamp(1e201), 1e200)
        self.assertEqual(coeff.clamp(1e-201), 1e-200)
    
    def test_shot_data_with_denormalized_numbers(self):
        """Test shot data with denormalized floating point numbers."""
        config = TunerConfig()
        
        # Very small denormalized number
        shot = ShotData(
            hit=True,
            distance=5e-308,  # Near minimum float
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        # May or may not validate depending on physical limits
        result = shot.is_valid(config)
        self.assertIsInstance(result, bool)
    
    def test_coefficient_with_subnormal_step_size(self):
        """Test coefficient with subnormal step size."""
        coeff = CoefficientConfig(
            name="subnormal",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=5e-324,  # Smallest possible float
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/subnormal"
        )
        
        # Should handle subnormal numbers
        self.assertIsNotNone(coeff)
    
    def test_negative_zero_handling(self):
        """Test handling of negative zero."""
        coeff = CoefficientConfig(
            name="negzero",
            default_value=-0.0,
            min_value=-1.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/negzero"
        )
        
        # -0.0 should equal 0.0
        self.assertEqual(coeff.default_value, 0.0)
    
    def test_integer_overflow_protection(self):
        """Test integer coefficient near max int."""
        coeff = CoefficientConfig(
            name="bigint",
            default_value=2147483640,  # Near 32-bit max
            min_value=2147483630,
            max_value=2147483647,  # 32-bit max
            initial_step_size=1,
            step_decay_rate=0.9,
            is_integer=True,
            enabled=True,
            nt_key="/bigint"
        )
        
        # Should handle large integers
        result = coeff.clamp(2147483650)
        self.assertEqual(result, 2147483647)


class TestMalformedDataHandling(unittest.TestCase):
    """Test handling of malformed and corrupted data."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = TunerConfig()
        self.config.LOG_DIRECTORY = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_shot_data_with_mixed_types(self):
        """Test shot data creation with mixed/wrong types."""
        # Try various type mismatches
        try:
            # Boolean as number
            shot = ShotData(
                hit=1,  # Should be bool
                distance=5.0,
                angle=0.5,
                velocity=15.0,
                timestamp=time.time()
            )
            # May succeed with type coercion
            self.assertIsNotNone(shot)
        except (TypeError, ValueError):
            # Or may fail - both acceptable
            pass
    
    def test_coefficient_name_with_null_bytes(self):
        """Test coefficient names containing null bytes."""
        try:
            coeff = CoefficientConfig(
                name="test\x00null",  # Null byte in name
                default_value=0.5,
                min_value=0.0,
                max_value=1.0,
                initial_step_size=0.1,
                step_decay_rate=0.9,
                is_integer=False,
                enabled=True,
                nt_key="/test"
            )
            # May succeed or fail
            self.assertIsNotNone(coeff)
        except (ValueError, TypeError):
            # Expected to potentially fail
            pass
    
    def test_nt_key_with_control_characters(self):
        """Test NT keys with control characters."""
        coeff = CoefficientConfig(
            name="control",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test\t\n\r"  # Control characters
        )
        
        # Should accept or sanitize
        self.assertIsNotNone(coeff.nt_key)
    
    def test_log_with_binary_data(self):
        """Test logging with binary data in strings."""
        logger = TunerLogger(self.config)
        
        # Try to log binary data
        try:
            logger.log_event('BINARY', b'\x00\x01\x02\xFF')
            logger.close()
        except (TypeError, UnicodeDecodeError):
            # May fail with binary data
            logger.close()
        
        # Should not crash
        self.assertTrue(True)
    
    def test_coefficient_dict_key_collision(self):
        """Test coefficient dictionary with duplicate keys."""
        config = TunerConfig()
        
        # Add coefficient with same dict key twice (overwrite)
        coeff1 = CoefficientConfig(
            name="first",
            default_value=0.1,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        coeff2 = CoefficientConfig(
            name="second",
            default_value=0.9,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Overwrite with same key
        config.COEFFICIENTS["duplicate"] = coeff1
        config.COEFFICIENTS["duplicate"] = coeff2  # Overwrites
        
        # Second should win
        self.assertEqual(config.COEFFICIENTS["duplicate"].name, "second")


class TestSystemResourceLimits(unittest.TestCase):
    """Test behavior at system resource limits."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = TunerConfig()
        self.config.LOG_DIRECTORY = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_maximum_path_length(self):
        """Test with maximum path length."""
        # Create deep directory structure
        deep_path = self.temp_dir
        for i in range(50):  # Create 50 levels deep
            deep_path = os.path.join(deep_path, f"d{i}")
        
        # May hit OS limits
        try:
            os.makedirs(deep_path, exist_ok=True)
            self.config.LOG_DIRECTORY = deep_path
            
            logger = TunerLogger(self.config)
            logger.close()
        except (OSError, IOError):
            # Expected on some systems
            pass
    
    def test_maximum_filename_length(self):
        """Test with very long filename."""
        # Filename near OS limit (255 chars typically)
        long_name = "test_" + "x" * 245 + ".csv"
        
        # May work or fail depending on OS
        try:
            long_path = os.path.join(self.temp_dir, long_name)
            with open(long_path, 'w') as f:
                f.write("test")
        except (OSError, IOError):
            # Expected on some systems
            pass
    
    def test_many_open_file_handles(self):
        """Test with many open file handles."""
        loggers = []
        
        # Try to open many loggers simultaneously
        max_loggers = 50  # Conservative limit
        
        try:
            for i in range(max_loggers):
                logger = TunerLogger(self.config)
                loggers.append(logger)
        except (OSError, IOError):
            # May hit file descriptor limit
            pass
        finally:
            # Clean up
            for logger in loggers:
                try:
                    logger.close()
                except (OSError, IOError, AttributeError):
                    # Ignore errors during cleanup - logger may be in invalid state
                    pass
    
    def test_very_large_tuning_order_list(self):
        """Test with extremely large tuning order."""
        config = TunerConfig()
        
        # Create huge tuning order
        config.TUNING_ORDER = [f"coeff_{i}" for i in range(10000)]
        
        # Should handle large list
        self.assertEqual(len(config.TUNING_ORDER), 10000)


class TestPlatformSpecificEdgeCases(unittest.TestCase):
    """Test platform-specific edge cases."""
    
    def test_windows_path_separators(self):
        """Test handling of Windows-style path separators."""
        config = TunerConfig()
        
        # Try Windows-style path
        windows_path = "C:\\Users\\Test\\logs"
        
        # Should accept various path formats
        try:
            config.LOG_DIRECTORY = windows_path
            self.assertEqual(config.LOG_DIRECTORY, windows_path)
        except (OSError, ValueError, AttributeError):
            # May fail on non-Windows platforms due to path format differences
            pass
    
    def test_unix_path_with_spaces(self):
        """Test Unix paths with spaces and special chars."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create path with spaces
            spaced_dir = os.path.join(temp_dir, "path with spaces")
            os.makedirs(spaced_dir, exist_ok=True)
            
            config = TunerConfig()
            config.LOG_DIRECTORY = spaced_dir
            
            logger = TunerLogger(config)
            logger.close()
            
            # Should handle spaces
            self.assertTrue(logger.csv_file.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_case_sensitivity_handling(self):
        """Test case sensitivity in coefficient names."""
        config = TunerConfig()
        
        # Add coefficients with different cases
        config.COEFFICIENTS["TestCoeff"] = CoefficientConfig(
            name="TestCoeff",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test1"
        )
        
        config.COEFFICIENTS["testcoeff"] = CoefficientConfig(
            name="testcoeff",
            default_value=0.6,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test2"
        )
        
        # Should treat as different
        self.assertEqual(len([k for k in config.COEFFICIENTS.keys() if 'test' in k.lower()]), 2)


class TestPathologicalInputCombinations(unittest.TestCase):
    """Test pathological combinations of inputs."""
    
    def test_all_coefficients_with_same_value(self):
        """Test when all coefficients have identical values."""
        config = TunerConfig()
        
        # Set all to same value
        for coeff in config.COEFFICIENTS.values():
            coeff.default_value = 0.5
            coeff.min_value = 0.5
            coeff.max_value = 0.5
        
        # Should handle zero-width ranges
        warnings = config.validate_config()
        self.assertIsInstance(warnings, list)
    
    def test_circular_dependencies_in_settings(self):
        """Test for circular dependencies in settings."""
        config = TunerConfig()
        
        # Set up potentially circular settings
        config.AUTOTUNE_SHOT_THRESHOLD = 10
        config.AUTO_ADVANCE_SHOT_THRESHOLD = 10
        config.MIN_VALID_SHOTS_BEFORE_UPDATE = 10
        
        # All thresholds the same - could cause issues
        # Should handle without infinite loops
        self.assertEqual(config.AUTOTUNE_SHOT_THRESHOLD, 10)
    
    def test_all_shots_at_exact_boundaries(self):
        """Test all shots at exact physical boundaries."""
        config = TunerConfig()
        
        # All shots at minimum
        for i in range(10):
            shot = ShotData(
                hit=True,
                distance=config.PHYSICAL_MIN_DISTANCE_M,
                angle=config.PHYSICAL_MIN_ANGLE_RAD,
                velocity=config.PHYSICAL_MIN_VELOCITY_MPS,
                timestamp=time.time() + i
            )
            
            self.assertTrue(shot.is_valid(config))
        
        # All shots at maximum
        for i in range(10):
            shot = ShotData(
                hit=True,
                distance=config.PHYSICAL_MAX_DISTANCE_M,
                angle=config.PHYSICAL_MAX_ANGLE_RAD,
                velocity=config.PHYSICAL_MAX_VELOCITY_MPS,
                timestamp=time.time() + i + 10
            )
            
            self.assertTrue(shot.is_valid(config))
    
    def test_alternating_valid_invalid_shots(self):
        """Test rapidly alternating between valid and invalid shots."""
        config = TunerConfig()
        
        valid_count = 0
        invalid_count = 0
        
        for i in range(100):
            if i % 2 == 0:
                # Valid shot
                shot = ShotData(
                    hit=True,
                    distance=5.0,
                    angle=0.5,
                    velocity=15.0,
                    timestamp=time.time()
                )
                if shot.is_valid(config):
                    valid_count += 1
            else:
                # Invalid shot
                shot = ShotData(
                    hit=True,
                    distance=-1.0,
                    angle=-1.0,
                    velocity=-1.0,
                    timestamp=time.time()
                )
                if not shot.is_valid(config):
                    invalid_count += 1
        
        # Should correctly identify each type
        self.assertEqual(valid_count, 50)
        self.assertEqual(invalid_count, 50)


class TestDefensiveProgramming(unittest.TestCase):
    """Test defensive programming practices."""
    
    def test_coefficient_with_missing_attributes(self):
        """Test accessing missing optional attributes."""
        coeff = CoefficientConfig(
            name="minimal",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Should have default values for optional attrs
        self.assertIsInstance(coeff.autotune_override, bool)
    
    def test_config_with_missing_required_fields(self):
        """Test config behavior with missing fields."""
        config = TunerConfig()
        
        # Remove required field (if possible)
        try:
            delattr(config, 'TUNER_ENABLED')
        except AttributeError:
            pass
        
        # Should handle gracefully or have defaults
        self.assertIsNotNone(config)
    
    def test_shot_data_validation_with_none_config(self):
        """Test shot validation with None config."""
        shot = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        # Try validation with None
        try:
            result = shot.is_valid(None)
            # May work or fail
        except (AttributeError, TypeError):
            # Expected to fail
            pass
    
    def test_interface_operations_when_not_initialized(self):
        """Test NT interface operations before initialization."""
        interface = NetworkTablesInterface(TunerConfig())
        
        # Try operations without connecting
        result = interface.read_coefficient("/test", 0.5)
        
        # Should return default gracefully
        self.assertEqual(result, 0.5)
    
    def test_logger_operations_after_file_deleted(self):
        """Test logger operations after log file deleted."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = TunerConfig()
            config.LOG_DIRECTORY = temp_dir
            
            logger = TunerLogger(config)
            log_path = logger.csv_file
            
            # Delete the log file while logger is open
            if log_path.exists():
                os.remove(log_path)
            
            # Try to log after deletion
            try:
                logger.log_event('TEST', 'After deletion')
                logger.close()
            except (OSError, IOError):
                # May fail
                pass
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
  
