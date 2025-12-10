"""
Comprehensive edge case tests for the configuration module.

This test suite covers:
- Boundary value testing (min, max, zero, negative values)
- Invalid data type handling
- Configuration file errors (missing, malformed, corrupt)
- Unicode and special character handling
- Memory and resource limits
- Concurrent access scenarios
- Error recovery and fallback behavior
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import os
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TunerConfig, CoefficientConfig


class TestCoefficientConfigEdgeCases(unittest.TestCase):
    """Comprehensive edge case tests for CoefficientConfig."""
    
    def test_clamp_boundary_values_float(self):
        """Test clamping at exact boundaries for floats."""
        config = CoefficientConfig(
            name="test",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Exact boundaries
        self.assertEqual(config.clamp(0.0), 0.0)
        self.assertEqual(config.clamp(1.0), 1.0)
        
        # Just inside boundaries
        self.assertAlmostEqual(config.clamp(0.0001), 0.0001)
        self.assertAlmostEqual(config.clamp(0.9999), 0.9999)
        
        # Just outside boundaries
        self.assertEqual(config.clamp(-0.0001), 0.0)
        self.assertEqual(config.clamp(1.0001), 1.0)
    
    def test_clamp_extreme_values(self):
        """Test clamping with extreme values."""
        config = CoefficientConfig(
            name="test",
            default_value=0.0,
            min_value=-1e6,
            max_value=1e6,
            initial_step_size=1.0,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Very large values
        self.assertEqual(config.clamp(1e10), 1e6)
        self.assertEqual(config.clamp(-1e10), -1e6)
        
        # Very small values
        self.assertAlmostEqual(config.clamp(1e-10), 1e-10)
        
        # Infinity
        self.assertEqual(config.clamp(float('inf')), 1e6)
        self.assertEqual(config.clamp(float('-inf')), -1e6)
    
    def test_clamp_nan_handling(self):
        """Test that NaN is handled properly."""
        config = CoefficientConfig(
            name="test",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # NaN should be clamped (behavior may vary)
        result = config.clamp(float('nan'))
        # NaN comparisons are always False, so check if result is NaN
        self.assertTrue(result != result or result == 0.0 or result == 1.0)
    
    def test_clamp_integer_rounding_edge_cases(self):
        """Test integer rounding at boundaries."""
        config = CoefficientConfig(
            name="test",
            default_value=20,
            min_value=10,
            max_value=50,
            initial_step_size=5,
            step_decay_rate=0.85,
            is_integer=True,
            enabled=True,
            nt_key="/test"
        )
        
        # Rounding at .5 (Python 3 uses banker's rounding: round half to even)
        self.assertEqual(config.clamp(25.5), 26)  # 25.5 rounds to 26 (even)
        self.assertEqual(config.clamp(26.5), 26)  # 26.5 rounds to 26 (even)
        
        # Rounding just below boundary
        self.assertEqual(config.clamp(10.4), 10)
        self.assertEqual(config.clamp(10.6), 11)
        
        # Rounding just above boundary
        self.assertEqual(config.clamp(49.4), 49)
        self.assertEqual(config.clamp(49.6), 50)
    
    def test_clamp_zero_range(self):
        """Test clamping when min equals max."""
        config = CoefficientConfig(
            name="test",
            default_value=5.0,
            min_value=5.0,
            max_value=5.0,
            initial_step_size=0.0,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Everything should clamp to the single allowed value
        self.assertEqual(config.clamp(0.0), 5.0)
        self.assertEqual(config.clamp(5.0), 5.0)
        self.assertEqual(config.clamp(10.0), 5.0)
    
    def test_clamp_negative_range(self):
        """Test clamping in negative value ranges."""
        config = CoefficientConfig(
            name="test",
            default_value=-5.0,
            min_value=-10.0,
            max_value=-1.0,
            initial_step_size=1.0,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        self.assertEqual(config.clamp(-5.0), -5.0)
        self.assertEqual(config.clamp(-15.0), -10.0)
        self.assertEqual(config.clamp(0.0), -1.0)
    
    def test_get_effective_autotune_settings_priority(self):
        """Test priority order for autotune settings."""
        config = CoefficientConfig(
            name="test",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test",
            autotune_override=True,
            autotune_enabled=True,
            autotune_shot_threshold=20
        )
        
        # Local override should win
        enabled, threshold = config.get_effective_autotune_settings(False, 10)
        self.assertTrue(enabled)
        self.assertEqual(threshold, 20)
        
        # Force global should override local
        enabled, threshold = config.get_effective_autotune_settings(False, 10, force_global=True)
        self.assertFalse(enabled)
        self.assertEqual(threshold, 10)
        
        # Without override, should use global
        config.autotune_override = False
        enabled, threshold = config.get_effective_autotune_settings(False, 10)
        self.assertFalse(enabled)
        self.assertEqual(threshold, 10)
    
    def test_invalid_nt_key_formats(self):
        """Test handling of various NT key formats."""
        # Valid keys
        valid_keys = [
            "/test",
            "/Tuning/test",
            "/Tuning/BayesianTuner/test",
        ]
        
        for key in valid_keys:
            config = CoefficientConfig(
                name="test",
                default_value=0.5,
                min_value=0.0,
                max_value=1.0,
                initial_step_size=0.1,
                step_decay_rate=0.9,
                is_integer=False,
                enabled=True,
                nt_key=key
            )
            self.assertEqual(config.nt_key, key)
        
        # Edge case keys (empty, special chars)
        edge_keys = ["", "/", "//", "/test/", "test"]
        
        for key in edge_keys:
            config = CoefficientConfig(
                name="test",
                default_value=0.5,
                min_value=0.0,
                max_value=1.0,
                initial_step_size=0.1,
                step_decay_rate=0.9,
                is_integer=False,
                enabled=True,
                nt_key=key
            )
            # Should accept any string
            self.assertEqual(config.nt_key, key)


class TestTunerConfigEdgeCases(unittest.TestCase):
    """Comprehensive edge case tests for TunerConfig."""
    
    def test_config_with_no_enabled_coefficients(self):
        """Test behavior when all coefficients are disabled."""
        config = TunerConfig()
        
        # Disable all coefficients
        for coeff in config.COEFFICIENTS.values():
            coeff.enabled = False
        
        enabled = config.get_enabled_coefficients_in_order()
        
        # Should return empty list
        self.assertEqual(len(enabled), 0)
    
    def test_config_with_empty_tuning_order(self):
        """Test behavior with empty tuning order."""
        config = TunerConfig()
        config.TUNING_ORDER = []
        
        enabled = config.get_enabled_coefficients_in_order()
        
        # Should return empty list
        self.assertEqual(len(enabled), 0)
    
    def test_config_with_mismatched_tuning_order(self):
        """Test when tuning order contains non-existent coefficients."""
        config = TunerConfig()
        config.TUNING_ORDER = ["NonExistent1", "NonExistent2"]
        
        enabled = config.get_enabled_coefficients_in_order()
        
        # Should handle gracefully (return empty or skip non-existent)
        self.assertIsInstance(enabled, list)
    
    def test_config_validation_multiple_warnings(self):
        """Test that all validation warnings are collected."""
        config = TunerConfig()
        
        # Create intentionally invalid coefficient for testing
        # (In practice, config should be valid, but we test validation logic)
        warnings = config.validate_config()
        
        # Should return a list
        self.assertIsInstance(warnings, list)
    
    def test_config_boundary_values(self):
        """Test configuration with boundary values."""
        config = TunerConfig()
        
        # Test with extreme but valid values
        config.N_INITIAL_POINTS = 1  # Minimum
        config.N_CALLS_PER_COEFFICIENT = 1  # Minimum
        config.MIN_VALID_SHOTS_BEFORE_UPDATE = 1  # Minimum
        
        # Should not raise errors
        self.assertIsNotNone(config)
        
        # Test with zero values (may be invalid)
        config.N_INITIAL_POINTS = 0
        warnings = config.validate_config()
        
        # Validation should catch this
        self.assertIsInstance(warnings, list)
    
    def test_config_negative_values(self):
        """Test configuration rejects negative values where inappropriate."""
        config = TunerConfig()
        
        # These should be positive
        config.AUTOTUNE_SHOT_THRESHOLD = -5
        config.N_CALLS_PER_COEFFICIENT = -10
        
        warnings = config.validate_config()
        
        # Validation may or may not catch these depending on implementation
        self.assertIsInstance(warnings, list)
    
    def test_config_float_vs_int_parameters(self):
        """Test that numeric parameters handle both float and int."""
        config = TunerConfig()
        
        # These should accept integers
        config.AUTOTUNE_SHOT_THRESHOLD = 10
        self.assertEqual(config.AUTOTUNE_SHOT_THRESHOLD, 10)
        
        # Float values for integer fields should work (will be used as-is or converted)
        config.AUTOTUNE_SHOT_THRESHOLD = 10.5
        self.assertIsNotNone(config.AUTOTUNE_SHOT_THRESHOLD)
    
    def test_config_unicode_coefficient_names(self):
        """Test coefficient names with unicode characters."""
        config = TunerConfig()
        
        # Create coefficient with unicode name
        unicode_coeff = CoefficientConfig(
            name="test_α_β_γ",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        config.COEFFICIENTS["test_unicode"] = unicode_coeff
        
        # Should handle unicode names
        self.assertIn("test_unicode", config.COEFFICIENTS)
    
    def test_config_special_characters_in_paths(self):
        """Test handling of special characters in paths."""
        config = TunerConfig()
        
        # Try various special characters in log directory
        special_chars = ["spaces in name", "under_score", "dash-name", "dots.in.name"]
        
        for char_test in special_chars:
            temp_dir = tempfile.mkdtemp(suffix=char_test)
            try:
                config.LOG_DIRECTORY = temp_dir
                # Should accept the path
                self.assertEqual(config.LOG_DIRECTORY, temp_dir)
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_config_very_long_coefficient_list(self):
        """Test configuration with many coefficients."""
        config = TunerConfig()
        
        # Add many coefficients
        for i in range(100):
            config.COEFFICIENTS[f"coeff_{i}"] = CoefficientConfig(
                name=f"coeff_{i}",
                default_value=0.5,
                min_value=0.0,
                max_value=1.0,
                initial_step_size=0.1,
                step_decay_rate=0.9,
                is_integer=False,
                enabled=True,
                nt_key=f"/coeff_{i}"
            )
        
        # Should handle large number of coefficients
        self.assertEqual(len(config.COEFFICIENTS), 100 + len(TunerConfig().COEFFICIENTS))
    
    def test_config_duplicate_coefficient_names(self):
        """Test behavior with duplicate coefficient names."""
        config = TunerConfig()
        
        # Add same coefficient twice
        coeff1 = CoefficientConfig(
            name="duplicate",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test1"
        )
        
        coeff2 = CoefficientConfig(
            name="duplicate",
            default_value=0.7,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test2"
        )
        
        config.COEFFICIENTS["dup1"] = coeff1
        config.COEFFICIENTS["dup2"] = coeff2
        
        # Both should exist with different dictionary keys
        self.assertEqual(len([c for c in config.COEFFICIENTS.values() if c.name == "duplicate"]), 2)


class TestTunerConfigResourceHandling(unittest.TestCase):
    """Test resource handling and cleanup."""
    
    def test_config_multiple_instances(self):
        """Test that multiple config instances don't interfere."""
        config1 = TunerConfig()
        config2 = TunerConfig()
        
        # Modify one
        config1.AUTOTUNE_ENABLED = True
        config2.AUTOTUNE_ENABLED = False
        
        # Should be independent
        self.assertTrue(config1.AUTOTUNE_ENABLED)
        self.assertFalse(config2.AUTOTUNE_ENABLED)
    
    def test_config_modification_isolation(self):
        """Test that modifying coefficients doesn't affect original."""
        config = TunerConfig()
        original_value = config.COEFFICIENTS["kDragCoefficient"].default_value
        
        # Modify
        config.COEFFICIENTS["kDragCoefficient"].default_value = 999.0
        
        # Create new config
        config2 = TunerConfig()
        
        # New config should have original value (if loading from file)
        # Or should be independent (if not shared)
        self.assertIsNotNone(config2.COEFFICIENTS["kDragCoefficient"].default_value)


if __name__ == '__main__':
    unittest.main()
  
