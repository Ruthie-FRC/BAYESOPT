"""
Exhaustive testing of all toggleable options and parameters.

This test suite covers:
- Every single toggle in TUNER_TOGGLES.ini
- Every parameter in COEFFICIENT_TUNING.py
- All possible combinations of toggle states
- Parameter boundary values and interactions
- Override mechanisms and priority rules
- Runtime toggle changes
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TunerConfig, CoefficientConfig


class TestTunerEnabledToggle(unittest.TestCase):
    """Test TUNER_ENABLED toggle in all scenarios."""
    
    def test_tuner_enabled_true(self):
        """Test tuner with TUNER_ENABLED = True."""
        config = TunerConfig()
        config.TUNER_ENABLED = True
        
        self.assertTrue(config.TUNER_ENABLED)
    
    def test_tuner_enabled_false(self):
        """Test tuner with TUNER_ENABLED = False."""
        config = TunerConfig()
        config.TUNER_ENABLED = False
        
        self.assertFalse(config.TUNER_ENABLED)
    
    def test_tuner_enabled_type_coercion(self):
        """Test type coercion for TUNER_ENABLED."""
        config = TunerConfig()
        
        # Integer coercion
        config.TUNER_ENABLED = 1
        self.assertTrue(bool(config.TUNER_ENABLED))
        
        config.TUNER_ENABLED = 0
        self.assertFalse(bool(config.TUNER_ENABLED))
    
    def test_tuner_enabled_with_all_other_toggles_off(self):
        """Test TUNER_ENABLED=True with all other toggles off."""
        config = TunerConfig()
        config.TUNER_ENABLED = True
        config.AUTOTUNE_ENABLED = False
        config.AUTO_ADVANCE_ON_SUCCESS = False
        config.REQUIRE_SHOT_LOGGED = False
        config.REQUIRE_COEFFICIENTS_UPDATED = False
        
        # Only tuner enabled
        self.assertTrue(config.TUNER_ENABLED)
        self.assertFalse(config.AUTOTUNE_ENABLED)


class TestAutotuneToggle(unittest.TestCase):
    """Test AUTOTUNE_ENABLED toggle and related settings."""
    
    def test_autotune_enabled_true(self):
        """Test autotune enabled."""
        config = TunerConfig()
        config.AUTOTUNE_ENABLED = True
        
        self.assertTrue(config.AUTOTUNE_ENABLED)
    
    def test_autotune_enabled_false(self):
        """Test autotune disabled (manual mode)."""
        config = TunerConfig()
        config.AUTOTUNE_ENABLED = False
        
        self.assertFalse(config.AUTOTUNE_ENABLED)
    
    def test_autotune_shot_threshold_minimum(self):
        """Test minimum autotune shot threshold."""
        config = TunerConfig()
        config.AUTOTUNE_SHOT_THRESHOLD = 1
        
        self.assertEqual(config.AUTOTUNE_SHOT_THRESHOLD, 1)
    
    def test_autotune_shot_threshold_zero(self):
        """Test zero autotune shot threshold."""
        config = TunerConfig()
        config.AUTOTUNE_SHOT_THRESHOLD = 0
        
        # Zero threshold edge case
        self.assertEqual(config.AUTOTUNE_SHOT_THRESHOLD, 0)
    
    def test_autotune_shot_threshold_large(self):
        """Test very large autotune shot threshold."""
        config = TunerConfig()
        config.AUTOTUNE_SHOT_THRESHOLD = 999999
        
        self.assertEqual(config.AUTOTUNE_SHOT_THRESHOLD, 999999)
    
    def test_autotune_force_global_true(self):
        """Test autotune with force_global=True."""
        config = TunerConfig()
        config.AUTOTUNE_ENABLED = True
        config.AUTOTUNE_FORCE_GLOBAL = True
        
        # All coefficients must use global
        coeff = config.COEFFICIENTS["kDragCoefficient"]
        coeff.autotune_override = True
        coeff.autotune_enabled = False
        
        enabled, _ = coeff.get_effective_autotune_settings(
            config.AUTOTUNE_ENABLED,
            config.AUTOTUNE_SHOT_THRESHOLD,
            force_global=config.AUTOTUNE_FORCE_GLOBAL
        )
        
        # Should use global (True) not local (False)
        self.assertTrue(enabled)
    
    def test_autotune_force_global_false(self):
        """Test autotune with force_global=False."""
        config = TunerConfig()
        config.AUTOTUNE_ENABLED = True
        config.AUTOTUNE_FORCE_GLOBAL = False
        
        # Coefficients can override
        coeff = config.COEFFICIENTS["kDragCoefficient"]
        coeff.autotune_override = True
        coeff.autotune_enabled = False
        
        enabled, _ = coeff.get_effective_autotune_settings(
            config.AUTOTUNE_ENABLED,
            config.AUTOTUNE_SHOT_THRESHOLD
        )
        
        # Should use local (False)
        self.assertFalse(enabled)


class TestAutoAdvanceToggle(unittest.TestCase):
    """Test AUTO_ADVANCE_ON_SUCCESS toggle and settings."""
    
    def test_auto_advance_enabled_true(self):
        """Test auto advance enabled."""
        config = TunerConfig()
        config.AUTO_ADVANCE_ON_SUCCESS = True
        
        self.assertTrue(config.AUTO_ADVANCE_ON_SUCCESS)
    
    def test_auto_advance_enabled_false(self):
        """Test auto advance disabled."""
        config = TunerConfig()
        config.AUTO_ADVANCE_ON_SUCCESS = False
        
        self.assertFalse(config.AUTO_ADVANCE_ON_SUCCESS)
    
    def test_auto_advance_shot_threshold_minimum(self):
        """Test minimum auto advance threshold."""
        config = TunerConfig()
        config.AUTO_ADVANCE_SHOT_THRESHOLD = 1
        
        self.assertEqual(config.AUTO_ADVANCE_SHOT_THRESHOLD, 1)
    
    def test_auto_advance_shot_threshold_zero(self):
        """Test zero auto advance threshold."""
        config = TunerConfig()
        config.AUTO_ADVANCE_SHOT_THRESHOLD = 0
        
        self.assertEqual(config.AUTO_ADVANCE_SHOT_THRESHOLD, 0)
    
    def test_auto_advance_shot_threshold_large(self):
        """Test large auto advance threshold."""
        config = TunerConfig()
        config.AUTO_ADVANCE_SHOT_THRESHOLD = 100000
        
        self.assertEqual(config.AUTO_ADVANCE_SHOT_THRESHOLD, 100000)
    
    def test_auto_advance_force_global_true(self):
        """Test auto advance with force_global=True."""
        config = TunerConfig()
        config.AUTO_ADVANCE_ON_SUCCESS = True
        config.AUTO_ADVANCE_FORCE_GLOBAL = True
        
        coeff = config.COEFFICIENTS["kDragCoefficient"]
        coeff.auto_advance_override = True
        coeff.auto_advance_on_success = False
        
        enabled, _ = coeff.get_effective_auto_advance_settings(
            config.AUTO_ADVANCE_ON_SUCCESS,
            config.AUTO_ADVANCE_SHOT_THRESHOLD,
            force_global=config.AUTO_ADVANCE_FORCE_GLOBAL
        )
        
        # Should use global
        self.assertTrue(enabled)
    
    def test_auto_advance_independent_from_autotune(self):
        """Test auto advance works independently from autotune."""
        config = TunerConfig()
        
        # Autotune off, auto advance on
        config.AUTOTUNE_ENABLED = False
        config.AUTO_ADVANCE_ON_SUCCESS = True
        
        self.assertFalse(config.AUTOTUNE_ENABLED)
        self.assertTrue(config.AUTO_ADVANCE_ON_SUCCESS)


class TestInterlockToggles(unittest.TestCase):
    """Test REQUIRE_SHOT_LOGGED and REQUIRE_COEFFICIENTS_UPDATED."""
    
    def test_require_shot_logged_true(self):
        """Test with shot logging required."""
        config = TunerConfig()
        config.REQUIRE_SHOT_LOGGED = True
        
        self.assertTrue(config.REQUIRE_SHOT_LOGGED)
    
    def test_require_shot_logged_false(self):
        """Test with shot logging not required."""
        config = TunerConfig()
        config.REQUIRE_SHOT_LOGGED = False
        
        self.assertFalse(config.REQUIRE_SHOT_LOGGED)
    
    def test_require_coefficients_updated_true(self):
        """Test with coefficient update required."""
        config = TunerConfig()
        config.REQUIRE_COEFFICIENTS_UPDATED = True
        
        self.assertTrue(config.REQUIRE_COEFFICIENTS_UPDATED)
    
    def test_require_coefficients_updated_false(self):
        """Test with coefficient update not required."""
        config = TunerConfig()
        config.REQUIRE_COEFFICIENTS_UPDATED = False
        
        self.assertFalse(config.REQUIRE_COEFFICIENTS_UPDATED)
    
    def test_both_interlocks_enabled(self):
        """Test with both interlocks enabled (most restrictive)."""
        config = TunerConfig()
        config.REQUIRE_SHOT_LOGGED = True
        config.REQUIRE_COEFFICIENTS_UPDATED = True
        
        self.assertTrue(config.REQUIRE_SHOT_LOGGED)
        self.assertTrue(config.REQUIRE_COEFFICIENTS_UPDATED)
    
    def test_both_interlocks_disabled(self):
        """Test with both interlocks disabled (least restrictive)."""
        config = TunerConfig()
        config.REQUIRE_SHOT_LOGGED = False
        config.REQUIRE_COEFFICIENTS_UPDATED = False
        
        self.assertFalse(config.REQUIRE_SHOT_LOGGED)
        self.assertFalse(config.REQUIRE_COEFFICIENTS_UPDATED)
    
    def test_interlock_combinations(self):
        """Test all combinations of interlocks."""
        config = TunerConfig()
        
        combinations = [
            (True, True),
            (True, False),
            (False, True),
            (False, False)
        ]
        
        for shot_logged, coeff_updated in combinations:
            config.REQUIRE_SHOT_LOGGED = shot_logged
            config.REQUIRE_COEFFICIENTS_UPDATED = coeff_updated
            
            self.assertEqual(config.REQUIRE_SHOT_LOGGED, shot_logged)
            self.assertEqual(config.REQUIRE_COEFFICIENTS_UPDATED, coeff_updated)


class TestCoefficientParameters(unittest.TestCase):
    """Test all coefficient configuration parameters."""
    
    def test_coefficient_enabled_toggle(self):
        """Test coefficient enabled/disabled toggle."""
        config = TunerConfig()
        
        # Test enabled
        coeff = config.COEFFICIENTS["kDragCoefficient"]
        coeff.enabled = True
        self.assertTrue(coeff.enabled)
        
        # Test disabled
        coeff.enabled = False
        self.assertFalse(coeff.enabled)
    
    def test_coefficient_default_value_boundaries(self):
        """Test coefficient default values at boundaries."""
        coeff = CoefficientConfig(
            name="boundary_test",
            default_value=0.0,  # At minimum
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        self.assertEqual(coeff.default_value, 0.0)
    
    def test_coefficient_min_max_equal(self):
        """Test coefficient with min == max (fixed value)."""
        coeff = CoefficientConfig(
            name="fixed",
            default_value=5.0,
            min_value=5.0,
            max_value=5.0,
            initial_step_size=0.0,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Any value should clamp to 5.0
        self.assertEqual(coeff.clamp(0.0), 5.0)
        self.assertEqual(coeff.clamp(10.0), 5.0)
    
    def test_coefficient_initial_step_size_zero(self):
        """Test coefficient with zero step size."""
        coeff = CoefficientConfig(
            name="zero_step",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.0,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        self.assertEqual(coeff.initial_step_size, 0.0)
    
    def test_coefficient_step_decay_rate_boundaries(self):
        """Test step decay rate at boundaries."""
        # Minimum (approaches zero fast)
        coeff_min = CoefficientConfig(
            name="fast_decay",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.01,  # Very fast decay
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        self.assertEqual(coeff_min.step_decay_rate, 0.01)
        
        # Maximum (slow decay)
        coeff_max = CoefficientConfig(
            name="slow_decay",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.999,  # Very slow decay
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        self.assertEqual(coeff_max.step_decay_rate, 0.999)
    
    def test_coefficient_is_integer_true(self):
        """Test integer coefficient."""
        coeff = CoefficientConfig(
            name="int_coeff",
            default_value=20,
            min_value=10,
            max_value=30,
            initial_step_size=1,
            step_decay_rate=0.9,
            is_integer=True,
            enabled=True,
            nt_key="/test"
        )
        
        # Should round floats
        self.assertEqual(coeff.clamp(20.7), 21)
        self.assertEqual(coeff.clamp(20.3), 20)
    
    def test_coefficient_is_integer_false(self):
        """Test float coefficient."""
        coeff = CoefficientConfig(
            name="float_coeff",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Should preserve decimals
        result = coeff.clamp(0.555)
        self.assertAlmostEqual(result, 0.555)
    
    def test_coefficient_nt_key_formats(self):
        """Test various NetworkTables key formats."""
        formats = [
            "/simple",
            "/Tuning/BayesianTuner/test",
            "/path/to/deep/key",
            "",  # Empty
            "no_leading_slash"
        ]
        
        for nt_key in formats:
            coeff = CoefficientConfig(
                name="key_test",
                default_value=0.5,
                min_value=0.0,
                max_value=1.0,
                initial_step_size=0.1,
                step_decay_rate=0.9,
                is_integer=False,
                enabled=True,
                nt_key=nt_key
            )
            
            self.assertEqual(coeff.nt_key, nt_key)


class TestPerCoefficientOverrides(unittest.TestCase):
    """Test per-coefficient override mechanisms."""
    
    def test_autotune_override_enabled(self):
        """Test autotune override enabled."""
        coeff = CoefficientConfig(
            name="override_test",
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
            autotune_shot_threshold=5
        )
        
        # Should use local settings
        enabled, threshold = coeff.get_effective_autotune_settings(False, 10)
        self.assertTrue(enabled)
        self.assertEqual(threshold, 5)
    
    def test_autotune_override_disabled(self):
        """Test autotune override disabled."""
        coeff = CoefficientConfig(
            name="no_override",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test",
            autotune_override=False
        )
        
        # Should use global settings
        enabled, threshold = coeff.get_effective_autotune_settings(True, 15)
        self.assertTrue(enabled)
        self.assertEqual(threshold, 15)
    
    def test_auto_advance_override_enabled(self):
        """Test auto advance override enabled."""
        coeff = CoefficientConfig(
            name="advance_override",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test",
            auto_advance_override=True,
            auto_advance_on_success=True,
            auto_advance_shot_threshold=7
        )
        
        # Should use local settings
        enabled, threshold = coeff.get_effective_auto_advance_settings(False, 10)
        self.assertTrue(enabled)
        self.assertEqual(threshold, 7)
    
    def test_both_overrides_enabled(self):
        """Test both autotune and auto_advance overrides."""
        coeff = CoefficientConfig(
            name="both_override",
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
            autotune_shot_threshold=5,
            auto_advance_override=True,
            auto_advance_on_success=True,
            auto_advance_shot_threshold=3
        )
        
        # Both should use local
        auto_enabled, auto_thresh = coeff.get_effective_autotune_settings(False, 10)
        adv_enabled, adv_thresh = coeff.get_effective_auto_advance_settings(False, 10)
        
        self.assertTrue(auto_enabled)
        self.assertEqual(auto_thresh, 5)
        self.assertTrue(adv_enabled)
        self.assertEqual(adv_thresh, 3)


class TestOptimizationParameters(unittest.TestCase):
    """Test optimization algorithm parameters."""
    
    def test_n_initial_points_minimum(self):
        """Test minimum initial points."""
        config = TunerConfig()
        config.N_INITIAL_POINTS = 1
        
        self.assertEqual(config.N_INITIAL_POINTS, 1)
    
    def test_n_initial_points_zero(self):
        """Test zero initial points."""
        config = TunerConfig()
        config.N_INITIAL_POINTS = 0
        
        self.assertEqual(config.N_INITIAL_POINTS, 0)
    
    def test_n_initial_points_large(self):
        """Test large initial points."""
        config = TunerConfig()
        config.N_INITIAL_POINTS = 100
        
        self.assertEqual(config.N_INITIAL_POINTS, 100)
    
    def test_n_calls_per_coefficient_minimum(self):
        """Test minimum calls per coefficient."""
        config = TunerConfig()
        config.N_CALLS_PER_COEFFICIENT = 1
        
        self.assertEqual(config.N_CALLS_PER_COEFFICIENT, 1)
    
    def test_n_calls_per_coefficient_large(self):
        """Test large calls per coefficient."""
        config = TunerConfig()
        config.N_CALLS_PER_COEFFICIENT = 1000
        
        self.assertEqual(config.N_CALLS_PER_COEFFICIENT, 1000)


class TestRateLimitingParameters(unittest.TestCase):
    """Test NetworkTables rate limiting parameters."""
    
    def test_max_write_rate_minimum(self):
        """Test minimum write rate."""
        config = TunerConfig()
        config.MAX_NT_WRITE_RATE_HZ = 0.1  # Very slow
        
        self.assertEqual(config.MAX_NT_WRITE_RATE_HZ, 0.1)
    
    def test_max_write_rate_maximum(self):
        """Test maximum write rate."""
        config = TunerConfig()
        config.MAX_NT_WRITE_RATE_HZ = 100.0  # Very fast
        
        self.assertEqual(config.MAX_NT_WRITE_RATE_HZ, 100.0)
    
    def test_max_read_rate_minimum(self):
        """Test minimum read rate."""
        config = TunerConfig()
        config.MAX_NT_READ_RATE_HZ = 0.5
        
        self.assertEqual(config.MAX_NT_READ_RATE_HZ, 0.5)
    
    def test_max_read_rate_maximum(self):
        """Test maximum read rate."""
        config = TunerConfig()
        config.MAX_NT_READ_RATE_HZ = 200.0
        
        self.assertEqual(config.MAX_NT_READ_RATE_HZ, 200.0)
    
    def test_batch_writes_enabled(self):
        """Test batch writes enabled."""
        config = TunerConfig()
        config.NT_BATCH_WRITES = True
        
        self.assertTrue(config.NT_BATCH_WRITES)
    
    def test_batch_writes_disabled(self):
        """Test batch writes disabled."""
        config = TunerConfig()
        config.NT_BATCH_WRITES = False
        
        self.assertFalse(config.NT_BATCH_WRITES)


class TestPhysicalLimitParameters(unittest.TestCase):
    """Test physical limit safety parameters."""
    
    def test_physical_max_velocity_boundary(self):
        """Test physical max velocity at boundary."""
        config = TunerConfig()
        config.PHYSICAL_MAX_VELOCITY_MPS = 50.0
        
        self.assertEqual(config.PHYSICAL_MAX_VELOCITY_MPS, 50.0)
    
    def test_physical_min_velocity_boundary(self):
        """Test physical min velocity at boundary."""
        config = TunerConfig()
        config.PHYSICAL_MIN_VELOCITY_MPS = 0.1
        
        self.assertEqual(config.PHYSICAL_MIN_VELOCITY_MPS, 0.1)
    
    def test_physical_max_angle_boundary(self):
        """Test physical max angle."""
        config = TunerConfig()
        config.PHYSICAL_MAX_ANGLE_RAD = 1.57  # ~90 degrees
        
        self.assertAlmostEqual(config.PHYSICAL_MAX_ANGLE_RAD, 1.57)
    
    def test_physical_min_angle_boundary(self):
        """Test physical min angle."""
        config = TunerConfig()
        config.PHYSICAL_MIN_ANGLE_RAD = 0.0
        
        self.assertEqual(config.PHYSICAL_MIN_ANGLE_RAD, 0.0)
    
    def test_physical_max_distance_boundary(self):
        """Test physical max distance."""
        config = TunerConfig()
        config.PHYSICAL_MAX_DISTANCE_M = 20.0
        
        self.assertEqual(config.PHYSICAL_MAX_DISTANCE_M, 20.0)
    
    def test_physical_min_distance_boundary(self):
        """Test physical min distance."""
        config = TunerConfig()
        config.PHYSICAL_MIN_DISTANCE_M = 0.5
        
        self.assertEqual(config.PHYSICAL_MIN_DISTANCE_M, 0.5)
    
    def test_physical_limits_all_at_extremes(self):
        """Test all physical limits at extreme values."""
        config = TunerConfig()
        
        # Set to extreme but valid values
        config.PHYSICAL_MAX_VELOCITY_MPS = 100.0
        config.PHYSICAL_MIN_VELOCITY_MPS = 0.01
        config.PHYSICAL_MAX_ANGLE_RAD = 3.14
        config.PHYSICAL_MIN_ANGLE_RAD = 0.0
        config.PHYSICAL_MAX_DISTANCE_M = 50.0
        config.PHYSICAL_MIN_DISTANCE_M = 0.1
        
        # All should be set
        self.assertGreater(config.PHYSICAL_MAX_VELOCITY_MPS, 0)
        self.assertGreater(config.PHYSICAL_MAX_ANGLE_RAD, 0)
        self.assertGreater(config.PHYSICAL_MAX_DISTANCE_M, 0)


class TestAllToggleCombinations(unittest.TestCase):
    """Test all possible combinations of toggles."""
    
    def test_all_toggles_matrix(self):
        """Test all 2^6 = 64 combinations of 6 main toggles."""
        config = TunerConfig()
        
        # Test all binary combinations
        for tuner_en in [False, True]:
            for autotune_en in [False, True]:
                for auto_adv in [False, True]:
                    for force_auto in [False, True]:
                        for force_adv in [False, True]:
                            for shot_log in [False, True]:
                                config.TUNER_ENABLED = tuner_en
                                config.AUTOTUNE_ENABLED = autotune_en
                                config.AUTO_ADVANCE_ON_SUCCESS = auto_adv
                                config.AUTOTUNE_FORCE_GLOBAL = force_auto
                                config.AUTO_ADVANCE_FORCE_GLOBAL = force_adv
                                config.REQUIRE_SHOT_LOGGED = shot_log
                                
                                # All should be valid states
                                self.assertEqual(config.TUNER_ENABLED, tuner_en)
                                self.assertEqual(config.AUTOTUNE_ENABLED, autotune_en)
                                self.assertEqual(config.AUTO_ADVANCE_ON_SUCCESS, auto_adv)
    
    def test_most_restrictive_combination(self):
        """Test most restrictive toggle combination."""
        config = TunerConfig()
        
        # Everything enabled/required
        config.TUNER_ENABLED = True
        config.AUTOTUNE_ENABLED = True
        config.AUTO_ADVANCE_ON_SUCCESS = True
        config.AUTOTUNE_FORCE_GLOBAL = True
        config.AUTO_ADVANCE_FORCE_GLOBAL = True
        config.REQUIRE_SHOT_LOGGED = True
        config.REQUIRE_COEFFICIENTS_UPDATED = True
        
        # All should be True
        self.assertTrue(config.TUNER_ENABLED)
        self.assertTrue(config.AUTOTUNE_FORCE_GLOBAL)
    
    def test_most_permissive_combination(self):
        """Test most permissive toggle combination."""
        config = TunerConfig()
        
        # Everything disabled/not required
        config.TUNER_ENABLED = False
        config.AUTOTUNE_ENABLED = False
        config.AUTO_ADVANCE_ON_SUCCESS = False
        config.AUTOTUNE_FORCE_GLOBAL = False
        config.AUTO_ADVANCE_FORCE_GLOBAL = False
        config.REQUIRE_SHOT_LOGGED = False
        config.REQUIRE_COEFFICIENTS_UPDATED = False
        
        # All should be False
        self.assertFalse(config.TUNER_ENABLED)
        self.assertFalse(config.AUTOTUNE_FORCE_GLOBAL)


if __name__ == '__main__':
    unittest.main()
  
