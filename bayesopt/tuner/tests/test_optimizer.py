"""
Unit tests for the optimizer module.
"""

import unittest
from unittest.mock import Mock, patch
import numpy as np

from tuner.config import TunerConfig, CoefficientConfig
from tuner.optimizer import BayesianOptimizer, CoefficientTuner
from tuner.nt_interface import ShotData


class TestBayesianOptimizer(unittest.TestCase):
    """Test BayesianOptimizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.coeff_config = self.config.COEFFICIENTS["kDragCoefficient"]
        self.optimizer = BayesianOptimizer(self.coeff_config, self.config)
    
    def test_initialization(self):
        """Test optimizer initialization."""
        self.assertEqual(self.optimizer.iteration, 0)
        self.assertEqual(self.optimizer.best_value, self.coeff_config.default_value)
        self.assertEqual(self.optimizer.current_step_size, self.coeff_config.initial_step_size)
    
    def test_suggest_next_value(self):
        """Test suggesting next value."""
        value = self.optimizer.suggest_next_value()
        
        # Should be within valid range
        self.assertGreaterEqual(value, self.coeff_config.min_value)
        self.assertLessEqual(value, self.coeff_config.max_value)
    
    def test_report_result(self):
        """Test reporting results."""
        value = 0.003
        
        # Report a hit
        self.optimizer.report_result(value, hit=True)
        
        self.assertEqual(self.optimizer.iteration, 1)
        self.assertEqual(len(self.optimizer.evaluation_history), 1)
        self.assertEqual(self.optimizer.evaluation_history[0]['value'], value)
        self.assertEqual(self.optimizer.evaluation_history[0]['hit'], True)
    
    def test_best_value_tracking(self):
        """Test that best value is tracked correctly."""
        # Report a miss
        self.optimizer.report_result(0.001, hit=False)
        first_best = self.optimizer.best_value
        
        # Report a hit - should become new best
        self.optimizer.report_result(0.003, hit=True)
        
        self.assertEqual(self.optimizer.best_value, 0.003)
        self.assertGreater(self.optimizer.best_score, -1.0)
    
    def test_convergence_max_iterations(self):
        """Test convergence based on max iterations."""
        # Run until max iterations
        for i in range(self.config.N_CALLS_PER_COEFFICIENT):
            value = self.optimizer.suggest_next_value()
            self.optimizer.report_result(value, hit=True)
        
        self.assertTrue(self.optimizer.is_converged())
    
    def test_step_size_decay(self):
        """Test step size decay over iterations."""
        initial_step = self.optimizer.current_step_size
        
        # Run several iterations
        for i in range(5):
            value = self.optimizer.suggest_next_value()
            self.optimizer.report_result(value, hit=True)
        
        # Step size should have decayed
        if self.config.STEP_SIZE_DECAY_ENABLED:
            self.assertLess(self.optimizer.current_step_size, initial_step)
    
    def test_integer_coefficient(self):
        """Test integer coefficient handling."""
        int_coeff = self.config.COEFFICIENTS["kVelocityIterationCount"]
        optimizer = BayesianOptimizer(int_coeff, self.config)
        
        value = optimizer.suggest_next_value()
        
        # Should be an integer
        self.assertEqual(value, int(value))
        self.assertGreaterEqual(value, int_coeff.min_value)
        self.assertLessEqual(value, int_coeff.max_value)
    
    def test_get_statistics(self):
        """Test getting optimization statistics."""
        # Run a few iterations
        for i in range(3):
            value = self.optimizer.suggest_next_value()
            self.optimizer.report_result(value, hit=(i % 2 == 0))
        
        stats = self.optimizer.get_statistics()
        
        self.assertIn('coefficient_name', stats)
        self.assertIn('iterations', stats)
        self.assertIn('best_value', stats)
        self.assertIn('hit_rate', stats)
        self.assertEqual(stats['iterations'], 3)


class TestCoefficientTuner(unittest.TestCase):
    """Test CoefficientTuner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.tuner = CoefficientTuner(self.config)
    
    def test_initialization(self):
        """Test tuner initialization."""
        self.assertEqual(self.tuner.current_index, 0)
        self.assertIsNotNone(self.tuner.current_optimizer)
        self.assertGreater(len(self.tuner.coefficients), 0)
    
    def test_get_current_coefficient_name(self):
        """Test getting current coefficient name."""
        name = self.tuner.get_current_coefficient_name()
        self.assertIsNotNone(name)
        self.assertIn(name, self.config.COEFFICIENTS)
    
    def test_suggest_coefficient_update(self):
        """Test suggesting coefficient updates."""
        suggestion = self.tuner.suggest_coefficient_update()
        
        self.assertIsNotNone(suggestion)
        self.assertEqual(len(suggestion), 2)
        
        coeff_name, value = suggestion
        self.assertIn(coeff_name, self.config.COEFFICIENTS)
        
        coeff = self.config.COEFFICIENTS[coeff_name]
        self.assertGreaterEqual(value, coeff.min_value)
        self.assertLessEqual(value, coeff.max_value)
    
    def test_record_shot_valid(self):
        """Test recording valid shot data."""
        shot_data = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=1234567890.0
        )
        
        coefficient_values = {
            coeff.name: coeff.default_value
            for coeff in self.config.COEFFICIENTS.values()
        }
        
        self.tuner.record_shot(shot_data, coefficient_values)
        
        # Should have pending shots
        self.assertGreater(len(self.tuner.pending_shots), 0)
    
    def test_record_shot_invalid(self):
        """Test recording invalid shot data."""
        # Invalid shot data (negative distance)
        shot_data = ShotData(
            hit=True,
            distance=-1.0,  # Invalid
            angle=0.5,
            velocity=15.0,
            timestamp=1234567890.0
        )
        
        coefficient_values = {}
        
        initial_invalid_count = self.tuner.consecutive_invalid_shots
        self.tuner.record_shot(shot_data, coefficient_values)
        
        # Should increment invalid counter
        self.assertGreater(self.tuner.consecutive_invalid_shots, initial_invalid_count)
    
    def test_shot_accumulation(self):
        """Test that shots are accumulated before processing."""
        coefficient_values = {
            coeff.name: coeff.default_value
            for coeff in self.config.COEFFICIENTS.values()
        }
        
        # Add shots one by one
        for i in range(self.config.MIN_VALID_SHOTS_BEFORE_UPDATE - 1):
            shot_data = ShotData(
                hit=True,
                distance=5.0,
                angle=0.5,
                velocity=15.0,
                timestamp=1234567890.0 + i
            )
            self.tuner.record_shot(shot_data, coefficient_values)
        
        # Should still have pending shots
        self.assertEqual(len(self.tuner.pending_shots), 
                        self.config.MIN_VALID_SHOTS_BEFORE_UPDATE - 1)
        
        # Add one more to trigger processing
        shot_data = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=1234567890.0 + 10
        )
        self.tuner.record_shot(shot_data, coefficient_values)
        
        # Pending shots should be cleared after processing
        self.assertEqual(len(self.tuner.pending_shots), 0)
    
    def test_is_complete(self):
        """Test completion detection."""
        # Initially not complete
        self.assertFalse(self.tuner.is_complete())
        
        # Simulate completing all coefficients
        self.tuner.current_optimizer = None
        self.tuner.current_index = len(self.tuner.coefficients)
        
        self.assertTrue(self.tuner.is_complete())
    
    def test_get_tuning_status(self):
        """Test getting tuning status."""
        status = self.tuner.get_tuning_status()
        
        self.assertIsInstance(status, str)
        self.assertGreater(len(status), 0)


if __name__ == '__main__':
    unittest.main()
    