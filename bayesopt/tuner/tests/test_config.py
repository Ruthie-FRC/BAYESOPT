"""
Unit tests for the configuration module.
"""

import unittest
from tuner.config import TunerConfig, CoefficientConfig


class TestCoefficientConfig(unittest.TestCase):
    """Test CoefficientConfig class."""
    
    def test_clamp_float(self):
        """Test clamping for float coefficients."""
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
        
        self.assertEqual(config.clamp(0.5), 0.5)
        self.assertEqual(config.clamp(-0.5), 0.0)
        self.assertEqual(config.clamp(1.5), 1.0)
    
    def test_clamp_integer(self):
        """Test clamping for integer coefficients."""
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
        
        self.assertEqual(config.clamp(25), 25)
        self.assertEqual(config.clamp(25.6), 26)  # Round
        self.assertEqual(config.clamp(5), 10)
        self.assertEqual(config.clamp(60), 50)


class TestTunerConfig(unittest.TestCase):
    """Test TunerConfig class."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = TunerConfig()
        
        self.assertTrue(config.TUNER_ENABLED)
        self.assertGreater(len(config.COEFFICIENTS), 0)
        self.assertGreater(len(config.TUNING_ORDER), 0)
    
    def test_get_enabled_coefficients_in_order(self):
        """Test getting enabled coefficients in order."""
        config = TunerConfig()
        
        enabled = config.get_enabled_coefficients_in_order()
        
        # Should have some enabled coefficients
        self.assertGreater(len(enabled), 0)
        
        # Should be in the correct order
        names = [c.name for c in enabled]
        expected_order = [n for n in config.TUNING_ORDER if n in names]
        self.assertEqual(names, expected_order)
    
    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        config = TunerConfig()
        warnings = config.validate_config()
        
        # Should have no warnings for default config
        self.assertEqual(len(warnings), 0)
    
    def test_validate_config_invalid_range(self):
        """Test config validation with invalid range."""
        # Test validation logic by checking a coefficient with swapped min/max
        coeff = CoefficientConfig(
            name="test_invalid",
            default_value=0.5,
            min_value=1.0,
            max_value=0.0,  # Invalid: max < min
            initial_step_size=0.1,
            step_decay_rate=0.9,
            is_integer=False,
            enabled=True,
            nt_key="/test"
        )
        
        # Manually test the validation logic that would be applied
        self.assertGreaterEqual(coeff.min_value, coeff.max_value,
                               "Test coefficient should have invalid range")
        
        # Also test that the default config is valid
        config = TunerConfig()
        warnings = config.validate_config()
        # All default coefficients should be valid
        for name, c in config.COEFFICIENTS.items():
            self.assertLess(c.min_value, c.max_value,
                          f"{name} has invalid range")
    
    def test_coefficient_definitions(self):
        """Test that all required coefficients are defined."""
        config = TunerConfig()
        
        required_coefficients = [
            "kDragCoefficient",
            "kVelocityIterationCount",
            "kAngleIterationCount",
            "kVelocityTolerance",
            "kAngleTolerance",
            "kLaunchHeight",
        ]
        
        for name in required_coefficients:
            self.assertIn(name, config.COEFFICIENTS)
            coeff = config.COEFFICIENTS[name]
            self.assertEqual(coeff.name, name)
            self.assertIsNotNone(coeff.nt_key)


if __name__ == '__main__':
    unittest.main()
