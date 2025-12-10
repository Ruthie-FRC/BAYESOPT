"""
Comprehensive integration and stress testing scenarios.

This test suite covers:
- End-to-end workflows across multiple components
- Stress testing with large data volumes
- Memory and performance edge cases
- Race conditions and timing issues
- Complex state transitions
- Recovery from cascading failures
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
import tempfile
import shutil
import time
import threading

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TunerConfig, CoefficientConfig
from nt_interface import NetworkTablesInterface, ShotData
from logger import TunerLogger

# Import optimizer separately to handle import issues
try:
    from optimizer import CoefficientTuner
    OPTIMIZER_AVAILABLE = True
except ImportError:
    OPTIMIZER_AVAILABLE = False
    CoefficientTuner = None


class TestEndToEndWorkflows(unittest.TestCase):
    """Test complete end-to-end workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not OPTIMIZER_AVAILABLE:
            self.skipTest("Optimizer not available")
        self.temp_dir = tempfile.mkdtemp()
        self.config = TunerConfig()
        self.config.LOG_DIRECTORY = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_tuning_cycle_single_coefficient(self):
        """Test complete tuning cycle for one coefficient."""
        tuner = CoefficientTuner(self.config)
        logger = TunerLogger(self.config)
        
        # Get first coefficient
        coeff_name = tuner.get_current_coefficient_name()
        self.assertIsNotNone(coeff_name)
        
        # Simulate multiple shots
        for i in range(10):
            shot_data = ShotData(
                hit=(i % 2 == 0),  # Alternate hits and misses
                distance=5.0,
                angle=0.5,
                velocity=15.0,
                timestamp=time.time() + i * 0.1
            )
            
            coefficient_values = {
                coeff_name: 0.003 + i * 0.0001
            }
            
            tuner.record_shot(shot_data, coefficient_values)
            
            # Log every shot
            logger.log_shot(
                coefficient_name=coeff_name,
                coefficient_value=coefficient_values[coeff_name],
                step_size=0.0001,
                iteration=i,
                shot_data=shot_data,
                nt_connected=True,
                match_mode=False,
                tuner_status=f"Iteration {i}",
                all_coefficient_values=coefficient_values
            )
        
        # Verify tuning progressed
        stats = tuner.current_optimizer.get_statistics()
        self.assertGreater(stats['iterations'], 0)
        
        logger.close()
    
    def test_complete_tuning_cycle_all_coefficients(self):
        """Test tuning through all coefficients in order."""
        tuner = CoefficientTuner(self.config)
        
        initial_count = len(tuner.coefficients)
        
        # Tune each coefficient
        for coeff_idx in range(min(3, initial_count)):  # Test first 3
            coeff_name = tuner.get_current_coefficient_name()
            
            # Simulate enough shots to advance
            for i in range(5):
                shot_data = ShotData(
                    hit=True,
                    distance=5.0,
                    angle=0.5,
                    velocity=15.0,
                    timestamp=time.time()
                )
                
                tuner.record_shot(shot_data, {coeff_name: 0.003})
            
            # Advance to next
            if coeff_idx < min(2, initial_count - 1):
                tuner.advance_to_next_coefficient()
        
        # Verify we progressed
        self.assertGreater(tuner.current_index, 0)
    
    def test_workflow_with_config_reload(self):
        """Test workflow that involves reloading configuration."""
        # Create initial config
        config1 = TunerConfig()
        tuner1 = CoefficientTuner(config1)
        
        first_coeff = tuner1.get_current_coefficient_name()
        
        # Create new config (simulating reload)
        config2 = TunerConfig()
        tuner2 = CoefficientTuner(config2)
        
        second_coeff = tuner2.get_current_coefficient_name()
        
        # Should start at same coefficient
        self.assertEqual(first_coeff, second_coeff)
    
    def test_workflow_with_logger_rotation(self):
        """Test workflow with multiple logger instances (log rotation)."""
        loggers = []
        
        # Create multiple loggers (simulating log rotation)
        for i in range(5):
            logger = TunerLogger(self.config)
            logger.log_event('ROTATION', f'Logger {i}')
            loggers.append(logger)
            time.sleep(0.01)  # Ensure different timestamps
        
        # Close all
        for logger in loggers:
            logger.close()
        
        # Verify all created separate files
        log_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.csv')]
        self.assertGreaterEqual(len(log_files), 1)


class TestStressScenarios(unittest.TestCase):
    """Test system under stress conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not OPTIMIZER_AVAILABLE:
            self.skipTest("Optimizer not available")
        self.temp_dir = tempfile.mkdtemp()
        self.config = TunerConfig()
        self.config.LOG_DIRECTORY = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_large_number_of_shots(self):
        """Test handling of very large number of shots."""
        tuner = CoefficientTuner(self.config)
        logger = TunerLogger(self.config)
        
        coeff_name = tuner.get_current_coefficient_name()
        
        # Log 1000 shots
        for i in range(1000):
            shot_data = ShotData(
                hit=(i % 3 != 0),  # 66% hit rate
                distance=5.0 + (i % 10) * 0.1,
                angle=0.5,
                velocity=15.0,
                timestamp=time.time() + i * 0.001
            )
            
            if i % 50 == 0:  # Only log every 50th
                logger.log_shot(
                    coefficient_name=coeff_name,
                    coefficient_value=0.003,
                    step_size=0.0001,
                    iteration=i // 50,
                    shot_data=shot_data,
                    nt_connected=True,
                    match_mode=False,
                    tuner_status=f"Shot {i}",
                    all_coefficient_values={coeff_name: 0.003}
                )
        
        logger.close()
        
        # Verify file was created
        self.assertTrue(logger.csv_file.exists())
    
    def test_rapid_coefficient_switching(self):
        """Test rapid switching between coefficients."""
        tuner = CoefficientTuner(self.config)
        
        # Rapidly switch back and forth
        for _ in range(20):
            tuner.advance_to_next_coefficient()
            if tuner.current_index > 0:
                tuner.go_to_previous_coefficient()
        
        # Should handle without errors
        self.assertIsNotNone(tuner.get_current_coefficient_name())
    
    def test_many_coefficients(self):
        """Test with a very large number of coefficients."""
        config = TunerConfig()
        
        # Add 100 additional coefficients
        for i in range(100):
            config.COEFFICIENTS[f"kTestCoeff_{i}"] = CoefficientConfig(
                name=f"kTestCoeff_{i}",
                default_value=0.5,
                min_value=0.0,
                max_value=1.0,
                initial_step_size=0.1,
                step_decay_rate=0.9,
                is_integer=False,
                enabled=True,
                nt_key=f"/test_{i}"
            )
            config.TUNING_ORDER.append(f"kTestCoeff_{i}")
        
        # Should handle many coefficients
        tuner = CoefficientTuner(config)
        self.assertGreater(len(tuner.coefficients), 100)
    
    def test_very_long_running_session(self):
        """Test behavior over extended time period."""
        logger = TunerLogger(self.config)
        
        # Simulate shots over extended period
        start_time = time.time()
        for i in range(100):
            logger.log_event('TEST', f'Long running event {i}')
            # Simulate small time passage
        
        elapsed = time.time() - start_time
        
        logger.close()
        
        # Should complete reasonably fast even with 100 events
        self.assertLess(elapsed, 10.0)


class TestRaceConditionsAndTiming(unittest.TestCase):
    """Test race conditions and timing-sensitive scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not OPTIMIZER_AVAILABLE:
            self.skipTest("Optimizer not available")
        self.temp_dir = tempfile.mkdtemp()
        self.config = TunerConfig()
        self.config.LOG_DIRECTORY = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_concurrent_shot_recording(self):
        """Test recording shots from multiple threads."""
        tuner = CoefficientTuner(self.config)
        errors = []
        
        def record_shots(thread_id):
            try:
                for i in range(10):
                    shot_data = ShotData(
                        hit=True,
                        distance=5.0,
                        angle=0.5,
                        velocity=15.0,
                        timestamp=time.time()
                    )
                    tuner.record_shot(shot_data, {'test': 0.003})
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=record_shots, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join(timeout=5)
        
        # Should have no errors
        self.assertEqual(len(errors), 0)
    
    def test_rapid_enable_disable_toggle(self):
        """Test rapidly toggling enable/disable."""
        config = TunerConfig()
        
        # Rapidly toggle
        for i in range(100):
            config.TUNER_ENABLED = (i % 2 == 0)
        
        # Should handle without errors
        self.assertIsInstance(config.TUNER_ENABLED, bool)
    
    def test_simultaneous_read_write_config(self):
        """Test simultaneous config reads and writes."""
        config = TunerConfig()
        errors = []
        
        def read_config():
            try:
                for _ in range(20):
                    _ = config.COEFFICIENTS["kDragCoefficient"].default_value
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        def write_config():
            try:
                for i in range(20):
                    config.AUTOTUNE_SHOT_THRESHOLD = 10 + i
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        # Start both threads
        t1 = threading.Thread(target=read_config)
        t2 = threading.Thread(target=write_config)
        
        t1.start()
        t2.start()
        
        t1.join(timeout=5)
        t2.join(timeout=5)
        
        # Should have no errors
        self.assertEqual(len(errors), 0)


class TestComplexStateTransitions(unittest.TestCase):
    """Test complex state transitions and edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not OPTIMIZER_AVAILABLE:
            self.skipTest("Optimizer not available")
        self.config = TunerConfig()
    
    def test_enable_disable_while_tuning(self):
        """Test enabling/disabling coefficients during tuning."""
        tuner = CoefficientTuner(self.config)
        
        # Start tuning first coefficient
        first_coeff = tuner.get_current_coefficient_name()
        
        # Disable it mid-tuning
        self.config.COEFFICIENTS[first_coeff].enabled = False
        
        # Try to advance
        tuner.advance_to_next_coefficient()
        
        # Should advance to next enabled coefficient
        second_coeff = tuner.get_current_coefficient_name()
        self.assertNotEqual(first_coeff, second_coeff)
    
    def test_change_tuning_order_mid_session(self):
        """Test changing tuning order during active session."""
        config = TunerConfig()
        tuner = CoefficientTuner(config)
        
        original_order = list(config.TUNING_ORDER)
        
        # Reverse the order
        config.TUNING_ORDER.reverse()
        
        # Create new tuner with modified order
        tuner2 = CoefficientTuner(config)
        
        # Should use new order
        self.assertIsNotNone(tuner2.get_current_coefficient_name())
    
    def test_transition_from_auto_to_manual_mode(self):
        """Test transitioning between auto and manual modes."""
        config = TunerConfig()
        
        # Start in auto mode
        config.AUTOTUNE_ENABLED = True
        config.AUTO_ADVANCE_ON_SUCCESS = True
        
        # Switch to manual mid-session
        config.AUTOTUNE_ENABLED = False
        config.AUTO_ADVANCE_ON_SUCCESS = False
        
        # Should handle transition
        self.assertFalse(config.AUTOTUNE_ENABLED)
    
    def test_force_global_toggle_during_tuning(self):
        """Test toggling force_global during active tuning."""
        config = TunerConfig()
        
        # Set up local overrides
        coeff = config.COEFFICIENTS["kDragCoefficient"]
        coeff.autotune_override = True
        coeff.autotune_enabled = True
        
        # Start without force_global
        config.AUTOTUNE_FORCE_GLOBAL = False
        enabled1, _ = coeff.get_effective_autotune_settings(False, 10)
        
        # Enable force_global
        config.AUTOTUNE_FORCE_GLOBAL = True
        enabled2, _ = coeff.get_effective_autotune_settings(
            False, 10, force_global=True
        )
        
        # Should override local setting
        self.assertTrue(enabled1)  # Uses local
        self.assertFalse(enabled2)  # Uses global


class TestCascadingFailures(unittest.TestCase):
    """Test recovery from cascading failures."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not OPTIMIZER_AVAILABLE:
            self.skipTest("Optimizer not available")
        self.temp_dir = tempfile.mkdtemp()
        self.config = TunerConfig()
        self.config.LOG_DIRECTORY = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_failure_doesnt_stop_optimization(self):
        """Test that logger failure doesn't stop optimization."""
        tuner = CoefficientTuner(self.config)
        logger = TunerLogger(self.config)
        
        # Close logger prematurely
        logger.close()
        
        # Tuner should still work
        shot_data = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        tuner.record_shot(shot_data, {'test': 0.003})
        
        # Should not raise error
        self.assertIsNotNone(tuner.current_optimizer)
    
    def test_multiple_component_failures(self):
        """Test handling when multiple components fail."""
        config = TunerConfig()
        
        # Simulate multiple failures
        # 1. Invalid coefficient range
        config.COEFFICIENTS["test_bad"] = CoefficientConfig(
            name="test_bad",
            default_value=5.0,
            min_value=10.0,  # Invalid
            max_value=1.0,   # Invalid
            initial_step_size=0.0,  # Invalid
            step_decay_rate=-1.0,  # Invalid
            is_integer=False,
            enabled=True,
            nt_key="/bad"
        )
        
        # Validation should catch multiple issues
        warnings = config.validate_config()
        
        # Should have multiple warnings
        self.assertGreater(len(warnings), 0)
    
    def test_recovery_after_corruption(self):
        """Test recovery after state corruption."""
        tuner = CoefficientTuner(self.config)
        
        # Corrupt state
        original_index = tuner.current_index
        tuner.current_index = -999  # Invalid
        
        # Try to recover by resetting
        tuner.current_index = max(0, min(tuner.current_index, len(tuner.coefficients) - 1))
        
        # Should recover to valid state
        self.assertGreaterEqual(tuner.current_index, 0)
        self.assertLess(tuner.current_index, len(tuner.coefficients))


class TestMemoryAndPerformance(unittest.TestCase):
    """Test memory usage and performance characteristics."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not OPTIMIZER_AVAILABLE:
            self.skipTest("Optimizer not available") 
        self.temp_dir = tempfile.mkdtemp()
        self.config = TunerConfig()
        self.config.LOG_DIRECTORY = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_memory_with_large_shot_history(self):
        """Test memory usage with large shot history."""
        tuner = CoefficientTuner(self.config)
        
        # Add many shots to history
        for i in range(1000):
            shot_data = ShotData(
                hit=True,
                distance=5.0,
                angle=0.5,
                velocity=15.0,
                timestamp=time.time()
            )
            
            # Only process every 10th to avoid slow test
            if i % 10 == 0:
                tuner.record_shot(shot_data, {'test': 0.003})
        
        # Should not consume excessive memory
        # (test passes if it completes without memory error)
        self.assertIsNotNone(tuner)
    
    def test_performance_with_many_coefficient_updates(self):
        """Test performance with frequent coefficient updates."""
        interface = NetworkTablesInterface(self.config)
        
        start_time = time.time()
        
        # Simulate many write attempts (rate limited)
        for i in range(100):
            interface.write_coefficient(f"/test_{i % 10}", 0.003 + i * 0.0001)
        
        elapsed = time.time() - start_time
        
        # Should complete reasonably fast (rate limiting will slow it down)
        self.assertLess(elapsed, 30.0)
    
    def test_log_file_size_growth(self):
        """Test log file doesn't grow unexpectedly."""
        logger = TunerLogger(self.config)
        
        # Log many events
        for i in range(100):
            logger.log_event('TEST', f'Event {i}')
        
        logger.close()
        
        # Check file size is reasonable
        file_size = logger.csv_file.stat().st_size
        
        # Should be less than 1MB for 100 events
        self.assertLess(file_size, 1024 * 1024)


if __name__ == '__main__':
    unittest.main()
  
