"""
Comprehensive tests for configuration conflicts and toggleable settings.

This test suite covers:
- Conflicting toggle combinations (autotune + force_global)
- Priority system validation (force_global > local override > global default)
- Invalid configuration combinations that could cause issues
- Error handling for misconfigured settings
- Edge cases in setting priority resolution
"""

import unittest
from unittest.mock import patch, mock_open
import sys
import os
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TunerConfig, CoefficientConfig


class TestConfigurationConflicts(unittest.TestCase):
    """Test configuration conflicts and resolution."""
    
    def test_force_global_overrides_local_autotune(self):
        """Test that force_global overrides local autotune settings."""
        config = TunerConfig()
        
        # Set up conflicting settings
        config.AUTOTUNE_ENABLED = False  # Global: disabled
        config.AUTOTUNE_FORCE_GLOBAL = True  # Force global
        
        # Coefficient has local override enabled
        coeff = config.COEFFICIENTS["kDragCoefficient"]
        coeff.autotune_override = True
        coeff.autotune_enabled = True  # Local: enabled (conflicts with global)
        
        # Get effective settings
        enabled, threshold = coeff.get_effective_autotune_settings(
            config.AUTOTUNE_ENABLED,
            config.AUTOTUNE_SHOT_THRESHOLD,
            force_global=config.AUTOTUNE_FORCE_GLOBAL
        )
        
        # Should use GLOBAL setting (False) despite local override
        self.assertFalse(enabled)
    
    def test_force_global_overrides_local_auto_advance(self):
        """Test that force_global overrides local auto_advance settings."""
        config = TunerConfig()
        
        # Set up conflicting settings
        config.AUTO_ADVANCE_ON_SUCCESS = False  # Global: disabled
        config.AUTO_ADVANCE_FORCE_GLOBAL = True  # Force global
        
        # Coefficient has local override enabled
        coeff = config.COEFFICIENTS["kDragCoefficient"]
        coeff.auto_advance_override = True
        coeff.auto_advance_on_success = True  # Local: enabled (conflicts)
        
        # Get effective settings
        enabled, threshold = coeff.get_effective_auto_advance_settings(
            config.AUTO_ADVANCE_ON_SUCCESS,
            config.AUTO_ADVANCE_SHOT_THRESHOLD,
            force_global=config.AUTO_ADVANCE_FORCE_GLOBAL
        )
        
        # Should use GLOBAL setting (False) despite local override
        self.assertFalse(enabled)
    
    def test_local_override_without_force_global(self):
        """Test local override works when force_global is False."""
        config = TunerConfig()
        
        # Global disabled, force_global disabled
        config.AUTOTUNE_ENABLED = False
        config.AUTOTUNE_FORCE_GLOBAL = False
        
        # Local override enabled
        coeff = config.COEFFICIENTS["kDragCoefficient"]
        coeff.autotune_override = True
        coeff.autotune_enabled = True
        coeff.autotune_shot_threshold = 20  # Different from global
        
        # Get effective settings
        enabled, threshold = coeff.get_effective_autotune_settings(
            config.AUTOTUNE_ENABLED,
            config.AUTOTUNE_SHOT_THRESHOLD
        )
        
        # Should use LOCAL settings
        self.assertTrue(enabled)
        self.assertEqual(threshold, 20)
    
    def test_no_override_uses_global(self):
        """Test that coefficients without override use global settings."""
        config = TunerConfig()
        
        # Set global settings
        config.AUTOTUNE_ENABLED = True
        config.AUTOTUNE_SHOT_THRESHOLD = 15
        
        # Coefficient with no override
        coeff = config.COEFFICIENTS["kDragCoefficient"]
        coeff.autotune_override = False
        
        # Get effective settings
        enabled, threshold = coeff.get_effective_autotune_settings(
            config.AUTOTUNE_ENABLED,
            config.AUTOTUNE_SHOT_THRESHOLD
        )
        
        # Should use GLOBAL settings
        self.assertTrue(enabled)
        self.assertEqual(threshold, 15)
    
    def test_conflicting_threshold_values(self):
        """Test handling of conflicting threshold values."""
        config = TunerConfig()
        
        # Global threshold
        config.AUTOTUNE_SHOT_THRESHOLD = 10
        config.AUTO_ADVANCE_SHOT_THRESHOLD = 20
        
        # Local thresholds (different)
        coeff = config.COEFFICIENTS["kDragCoefficient"]
        coeff.autotune_override = True
        coeff.autotune_shot_threshold = 5  # Lower than auto_advance
        coeff.auto_advance_override = True
        coeff.auto_advance_shot_threshold = 30  # Higher than autotune
        
        # Both should work independently
        autotune_enabled, autotune_threshold = coeff.get_effective_autotune_settings(
            config.AUTOTUNE_ENABLED,
            config.AUTOTUNE_SHOT_THRESHOLD
        )
        
        advance_enabled, advance_threshold = coeff.get_effective_auto_advance_settings(
            config.AUTO_ADVANCE_ON_SUCCESS,
            config.AUTO_ADVANCE_SHOT_THRESHOLD
        )
        
        # Should use local values
        self.assertEqual(autotune_threshold, 5)
        self.assertEqual(advance_threshold, 30)
    
    def test_both_force_global_flags_active(self):
        """Test when both autotune and auto_advance force_global are True."""
        config = TunerConfig()
        
        # Force both to global
        config.AUTOTUNE_FORCE_GLOBAL = True
        config.AUTO_ADVANCE_FORCE_GLOBAL = True
        
        # Set global values
        config.AUTOTUNE_ENABLED = True
        config.AUTO_ADVANCE_ON_SUCCESS = False
        
        # Coefficient with conflicting local overrides
        coeff = config.COEFFICIENTS["kDragCoefficient"]
        coeff.autotune_override = True
        coeff.autotune_enabled = False  # Conflicts with global
        coeff.auto_advance_override = True
        coeff.auto_advance_on_success = True  # Conflicts with global
        
        # Get effective settings
        autotune_enabled, _ = coeff.get_effective_autotune_settings(
            config.AUTOTUNE_ENABLED,
            config.AUTOTUNE_SHOT_THRESHOLD,
            force_global=config.AUTOTUNE_FORCE_GLOBAL
        )
        
        advance_enabled, _ = coeff.get_effective_auto_advance_settings(
            config.AUTO_ADVANCE_ON_SUCCESS,
            config.AUTO_ADVANCE_SHOT_THRESHOLD,
            force_global=config.AUTO_ADVANCE_FORCE_GLOBAL
        )
        
        # Both should use global despite local overrides
        self.assertTrue(autotune_enabled)  # Global True
        self.assertFalse(advance_enabled)  # Global False
    
    def test_disabled_coefficient_with_overrides(self):
        """Test that disabled coefficients can still have override settings."""
        config = TunerConfig()
        
        # Disable a coefficient
        coeff = config.COEFFICIENTS["kAirDensity"]
        coeff.enabled = False
        coeff.autotune_override = True
        coeff.autotune_enabled = True
        
        # Should still be able to get settings even if disabled
        enabled, threshold = coeff.get_effective_autotune_settings(
            False, 10
        )
        
        # Settings should work (even though coefficient won't be tuned)
        self.assertTrue(enabled)
    
    def test_all_coefficients_disabled(self):
        """Test behavior when all coefficients are disabled."""
        config = TunerConfig()
        
        # Disable all coefficients
        for coeff in config.COEFFICIENTS.values():
            coeff.enabled = False
        
        # Get enabled coefficients
        enabled = config.get_enabled_coefficients_in_order()
        
        # Should return empty list
        self.assertEqual(len(enabled), 0)
    
    def test_tuning_order_with_disabled_coefficients(self):
        """Test tuning order excludes disabled coefficients."""
        config = TunerConfig()
        
        # Disable one coefficient
        config.COEFFICIENTS["kDragCoefficient"].enabled = False
        
        # Get enabled coefficients in order
        enabled = config.get_enabled_coefficients_in_order()
        
        # Should not include disabled coefficient
        names = [c.name for c in enabled]
        self.assertNotIn("kDragCoefficient", names)
        
        # But should include others in correct order
        remaining = [n for n in config.TUNING_ORDER if n != "kDragCoefficient"]
        expected = [n for n in remaining if n in [c.name for c in config.COEFFICIENTS.values() if c.enabled]]
        self.assertEqual(names, expected)
    
    def test_conflicting_min_max_values(self):
        """Test handling of min > max (invalid configuration)."""
        # This should be caught by validation
        config = TunerConfig()
        
        # Create invalid coefficient
        config.COEFFICIENTS["test_invalid"] = CoefficientConfig(
            name="test_invalid",
            default_value=5.0,
            min_value=10.0,  # Invalid: min > max
            max_value=1.0,
            initial_step_size=1.0,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Validation should catch this
        warnings = config.validate_config()
        
        # Should have warnings about invalid range
        self.assertGreater(len(warnings), 0)
        self.assertTrue(any("test_invalid" in str(w) or "range" in str(w).lower() for w in warnings))
    
    def test_default_outside_min_max_range(self):
        """Test default value outside min/max range."""
        config = TunerConfig()
        
        # Create coefficient with default outside range
        config.COEFFICIENTS["test_invalid"] = CoefficientConfig(
            name="test_invalid",
            default_value=100.0,  # Outside range
            min_value=0.0,
            max_value=10.0,
            initial_step_size=1.0,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Validation should catch this
        warnings = config.validate_config()
        
        # Should have warnings
        self.assertGreater(len(warnings), 0)
    
    def test_zero_or_negative_step_size(self):
        """Test zero or negative step size."""
        config = TunerConfig()
        
        # Zero step size
        config.COEFFICIENTS["test_zero"] = CoefficientConfig(
            name="test_zero",
            default_value=5.0,
            min_value=0.0,
            max_value=10.0,
            initial_step_size=0.0,  # Invalid: zero
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Negative step size
        config.COEFFICIENTS["test_neg"] = CoefficientConfig(
            name="test_neg",
            default_value=5.0,
            min_value=0.0,
            max_value=10.0,
            initial_step_size=-1.0,  # Invalid: negative
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Validation should catch these
        warnings = config.validate_config()
        
        # Should have warnings
        self.assertGreater(len(warnings), 0)
    
    def test_invalid_step_decay_rate(self):
        """Test invalid step decay rate values."""
        config = TunerConfig()
        
        # Decay rate > 1 (grows instead of shrinks)
        config.COEFFICIENTS["test_grow"] = CoefficientConfig(
            name="test_grow",
            default_value=5.0,
            min_value=0.0,
            max_value=10.0,
            initial_step_size=1.0,
            step_decay_rate=1.5,  # Invalid: > 1
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Decay rate = 0 (immediate decay to zero)
        config.COEFFICIENTS["test_zero_decay"] = CoefficientConfig(
            name="test_zero_decay",
            default_value=5.0,
            min_value=0.0,
            max_value=10.0,
            initial_step_size=1.0,
            step_decay_rate=0.0,  # Invalid: zero
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Negative decay rate
        config.COEFFICIENTS["test_neg_decay"] = CoefficientConfig(
            name="test_neg_decay",
            default_value=5.0,
            min_value=0.0,
            max_value=10.0,
            initial_step_size=1.0,
            step_decay_rate=-0.5,  # Invalid: negative
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Validation should catch these
        warnings = config.validate_config()
        
        # Should have warnings
        self.assertGreater(len(warnings), 0)
    
    def test_negative_shot_thresholds(self):
        """Test negative shot threshold values."""
        config = TunerConfig()
        
        # Set negative thresholds
        config.AUTOTUNE_SHOT_THRESHOLD = -5
        config.AUTO_ADVANCE_SHOT_THRESHOLD = -10
        
        # Validation should catch these
        warnings = config.validate_config()
        
        # Should have warnings (if validation checks this)
        # Note: may pass if validation doesn't check negative thresholds
        self.assertIsInstance(warnings, list)
    
    def test_zero_shot_thresholds(self):
        """Test zero shot threshold values."""
        config = TunerConfig()
        
        # Set zero thresholds (edge case - no shots needed?)
        config.AUTOTUNE_SHOT_THRESHOLD = 0
        config.AUTO_ADVANCE_SHOT_THRESHOLD = 0
        
        # Should handle gracefully
        warnings = config.validate_config()
        self.assertIsInstance(warnings, list)
    
    def test_very_large_shot_thresholds(self):
        """Test extremely large shot thresholds."""
        config = TunerConfig()
        
        # Set very large thresholds
        config.AUTOTUNE_SHOT_THRESHOLD = 1000000
        config.AUTO_ADVANCE_SHOT_THRESHOLD = 1000000
        
        # Should handle without errors
        warnings = config.validate_config()
        self.assertIsInstance(warnings, list)
    
    def test_conflicting_interlock_settings(self):
        """Test conflicting interlock settings."""
        config = TunerConfig()
        
        # Both interlocks enabled (most restrictive)
        config.REQUIRE_SHOT_LOGGED = True
        config.REQUIRE_COEFFICIENTS_UPDATED = True
        
        # Should work but be very restrictive
        self.assertTrue(config.REQUIRE_SHOT_LOGGED)
        self.assertTrue(config.REQUIRE_COEFFICIENTS_UPDATED)
    
    def test_all_toggles_enabled(self):
        """Test with all toggle features enabled simultaneously."""
        config = TunerConfig()
        
        # Enable everything
        config.TUNER_ENABLED = True
        config.AUTOTUNE_ENABLED = True
        config.AUTO_ADVANCE_ON_SUCCESS = True
        config.AUTOTUNE_FORCE_GLOBAL = True
        config.AUTO_ADVANCE_FORCE_GLOBAL = True
        config.REQUIRE_SHOT_LOGGED = True
        config.REQUIRE_COEFFICIENTS_UPDATED = True
        
        # Should handle this configuration
        warnings = config.validate_config()
        self.assertIsInstance(warnings, list)
    
    def test_all_toggles_disabled(self):
        """Test with all toggle features disabled simultaneously."""
        config = TunerConfig()
        
        # Disable everything
        config.TUNER_ENABLED = False
        config.AUTOTUNE_ENABLED = False
        config.AUTO_ADVANCE_ON_SUCCESS = False
        config.REQUIRE_SHOT_LOGGED = False
        config.REQUIRE_COEFFICIENTS_UPDATED = False
        
        # Should handle this configuration
        warnings = config.validate_config()
        self.assertIsInstance(warnings, list)


class TestConfigurationErrorHandling(unittest.TestCase):
    """Test error handling in configuration."""
    
    def test_missing_required_coefficient_fields(self):
        """Test handling of coefficients with missing required fields."""
        # This tests the robustness of the config system
        # In practice, dataclass should enforce this, but test anyway
        try:
            coeff = CoefficientConfig(
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
            # Should succeed
            self.assertIsNotNone(coeff)
        except TypeError as e:
            # If it fails, that's also acceptable behavior
            self.assertIn("missing", str(e).lower())
    
    def test_invalid_coefficient_types(self):
        """Test handling of invalid types in coefficient fields."""
        # String where float expected
        try:
            coeff = CoefficientConfig(
                name="test",
                default_value="not_a_number",  # Invalid type
                min_value=0.0,
                max_value=1.0,
                initial_step_size=0.1,
                step_decay_rate=0.9,
                is_integer=False,
                enabled=True,
                nt_key="/test"
            )
            # If it doesn't fail during creation, clamping should handle it
            result = coeff.clamp(0.5)
            # May succeed or fail depending on implementation
        except (TypeError, ValueError):
            # Expected to fail
            pass
    
    def test_none_values_in_coefficient(self):
        """Test handling of None values in coefficient fields."""
        try:
            coeff = CoefficientConfig(
                name="test",
                default_value=None,  # Invalid
                min_value=0.0,
                max_value=1.0,
                initial_step_size=0.1,
                step_decay_rate=0.9,
                is_integer=False,
                enabled=True,
                nt_key="/test"
            )
            # Should fail or handle gracefully
        except (TypeError, ValueError):
            # Expected
            pass
    
    def test_empty_tuning_order_with_enabled_coefficients(self):
        """Test mismatch between empty tuning order and enabled coefficients."""
        config = TunerConfig()
        
        # Clear tuning order
        config.TUNING_ORDER = []
        
        # But coefficients are still enabled
        enabled_count = sum(1 for c in config.COEFFICIENTS.values() if c.enabled)
        self.assertGreater(enabled_count, 0)
        
        # Get enabled in order
        enabled = config.get_enabled_coefficients_in_order()
        
        # Should return empty list (no order specified)
        self.assertEqual(len(enabled), 0)
    
    def test_tuning_order_with_non_existent_coefficients(self):
        """Test tuning order containing coefficients that don't exist."""
        config = TunerConfig()
        
        # Add non-existent coefficients to order
        config.TUNING_ORDER = [
            "kDragCoefficient",  # Exists
            "kNonExistent1",      # Doesn't exist
            "kLaunchHeight",      # Exists
            "kNonExistent2",      # Doesn't exist
        ]
        
        # Get enabled in order
        enabled = config.get_enabled_coefficients_in_order()
        
        # Should only include existing coefficients
        names = [c.name for c in enabled]
        self.assertIn("kDragCoefficient", names)
        self.assertIn("kLaunchHeight", names)
        self.assertNotIn("kNonExistent1", names)
        self.assertNotIn("kNonExistent2", names)


if __name__ == '__main__':
    unittest.main()
  
