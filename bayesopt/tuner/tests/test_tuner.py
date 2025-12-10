"""
Unit tests for the BayesianTunerCoordinator module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import sys
import os
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TunerConfig
from nt_interface import ShotData
from tuner import BayesianTunerCoordinator


class TestBayesianTunerCoordinator(unittest.TestCase):
    """Test BayesianTunerCoordinator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        
        # Create temp directory for logs
        self.temp_dir = tempfile.mkdtemp()
        self.config.LOG_DIRECTORY = self.temp_dir
        
        # Create coordinator (hotkeys may or may not work depending on environment)
        self.coordinator = BayesianTunerCoordinator(self.config)
    
    def tearDown(self):
        """Clean up after tests."""
        if self.coordinator.running:
            self.coordinator.stop()
        
        # Clean up temp directory
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test coordinator initialization."""
        self.assertIsNotNone(self.coordinator.config)
        self.assertIsNotNone(self.coordinator.nt_interface)
        self.assertIsNotNone(self.coordinator.optimizer)
        self.assertIsNotNone(self.coordinator.data_logger)
        self.assertFalse(self.coordinator.running)
        self.assertIsNone(self.coordinator.thread)
    
    def test_initialization_with_custom_config(self):
        """Test initialization with custom config."""
        custom_config = TunerConfig()
        custom_config.TUNER_ENABLED = False
        temp_dir = tempfile.mkdtemp()
        custom_config.LOG_DIRECTORY = temp_dir
        
        coordinator = BayesianTunerCoordinator(custom_config)
        
        self.assertEqual(coordinator.config.TUNER_ENABLED, False)
        
        # Clean up
        shutil.rmtree(temp_dir)
    
    def test_initialization_validates_config(self):
        """Test that config is validated on initialization."""
        # Config validation should run without errors
        self.assertIsNotNone(self.coordinator.config)
        
        # Should have coefficient values dict
        self.assertIsInstance(self.coordinator.current_coefficient_values, dict)
        self.assertEqual(len(self.coordinator.current_coefficient_values), 0)
    
    def test_accumulated_shots_initialized(self):
        """Test that accumulated shots list is initialized."""
        self.assertIsInstance(self.coordinator.accumulated_shots, list)
        self.assertEqual(len(self.coordinator.accumulated_shots), 0)
    
    def test_runtime_enabled_from_config(self):
        """Test that runtime_enabled is initialized from config."""
        self.assertEqual(
            self.coordinator.runtime_enabled,
            self.coordinator.config.TUNER_ENABLED
        )
    
    def test_start_when_already_running(self):
        """Test that starting when already running does nothing."""
        # Mock to avoid actual NT connection
        with patch.object(self.coordinator.nt_interface, 'start', return_value=True):
            with patch.object(self.coordinator.nt_interface, 'read_all_coefficients', return_value={}):
                self.coordinator.config.TUNER_ENABLED = True
                self.coordinator.start()
                
                # Try starting again
                initial_thread = self.coordinator.thread
                self.coordinator.start()
                
                # Should be the same thread
                self.assertEqual(self.coordinator.thread, initial_thread)
                
                # Clean up
                self.coordinator.stop()
    
    def test_start_when_disabled(self):
        """Test that start does nothing when tuner is disabled."""
        self.coordinator.config.TUNER_ENABLED = False
        self.coordinator.start()
        
        self.assertFalse(self.coordinator.running)
        self.assertIsNone(self.coordinator.thread)
    
    def test_start_nt_connection_failure(self):
        """Test behavior when NT connection fails on start."""
        self.coordinator.config.TUNER_ENABLED = True
        
        # Mock NT connection to fail
        with patch.object(self.coordinator.nt_interface, 'start', return_value=False):
            self.coordinator.start()
        
        self.assertFalse(self.coordinator.running)
        self.assertIsNone(self.coordinator.thread)
    
    @patch('time.sleep')
    def test_stop_when_not_running(self, mock_sleep):
        """Test that stop handles not running gracefully."""
        self.assertFalse(self.coordinator.running)
        
        # Should not raise error
        self.coordinator.stop()
        
        self.assertFalse(self.coordinator.running)
    
    @patch('time.sleep')
    def test_stop_closes_logger(self, mock_sleep):
        """Test that stop closes the logger."""
        # Mock starting
        with patch.object(self.coordinator.nt_interface, 'start', return_value=True):
            with patch.object(self.coordinator.nt_interface, 'read_all_coefficients', return_value={}):
                self.coordinator.config.TUNER_ENABLED = True
                self.coordinator.start()
                
                # Verify running
                self.assertTrue(self.coordinator.running)
                
                # Mock close method
                with patch.object(self.coordinator.data_logger, 'close') as mock_close:
                    self.coordinator.stop()
                    
                    # Verify logger close was called
                    mock_close.assert_called_once()
    
    def test_check_safety_conditions_match_mode(self):
        """Test safety check blocks execution in match mode."""
        # Mock match mode
        with patch.object(self.coordinator.nt_interface, 'is_match_mode', return_value=True):
            result = self.coordinator._check_safety_conditions()
        
        self.assertFalse(result)
    
    def test_check_safety_conditions_runtime_disabled(self):
        """Test safety check blocks when runtime disabled."""
        self.coordinator.runtime_enabled = False
        
        result = self.coordinator._check_safety_conditions()
        
        self.assertFalse(result)
    
    def test_check_safety_conditions_not_connected(self):
        """Test safety check blocks when not connected."""
        self.coordinator.runtime_enabled = True
        
        with patch.object(self.coordinator.nt_interface, 'is_match_mode', return_value=False):
            with patch.object(self.coordinator.nt_interface, 'is_connected', return_value=False):
                result = self.coordinator._check_safety_conditions()
        
        self.assertFalse(result)
    
    def test_check_safety_conditions_all_good(self):
        """Test safety check passes when all conditions met."""
        self.coordinator.runtime_enabled = True
        
        with patch.object(self.coordinator.nt_interface, 'is_match_mode', return_value=False):
            with patch.object(self.coordinator.nt_interface, 'is_connected', return_value=True):
                result = self.coordinator._check_safety_conditions()
        
        self.assertTrue(result)
    
    def test_accumulate_shot_valid_data(self):
        """Test accumulating valid shot data."""
        shot_data = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        self.coordinator.current_coefficient_values = {
            'kDragCoefficient': 0.003,
            'kLaunchHeight': 0.8
        }
        
        initial_count = len(self.coordinator.accumulated_shots)
        self.coordinator._accumulate_shot(shot_data)
        
        self.assertEqual(len(self.coordinator.accumulated_shots), initial_count + 1)
        
        # Verify shot was logged
        accumulated = self.coordinator.accumulated_shots[-1]
        self.assertEqual(accumulated['shot_data'], shot_data)
        self.assertEqual(accumulated['coefficient_values'], self.coordinator.current_coefficient_values)
    
    def test_accumulate_shot_invalid_data(self):
        """Test that invalid shot data is handled correctly."""
        shot_data = ShotData(
            hit=True,
            distance=-1.0,  # Invalid
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        initial_count = len(self.coordinator.accumulated_shots)
        
        # Accumulate the shot
        self.coordinator._accumulate_shot(shot_data)
        
        # Shot is accumulated for logging purposes
        # The optimizer will handle validation when processing
        self.assertEqual(len(self.coordinator.accumulated_shots), initial_count + 1)
    
    def test_check_optimization_trigger_manual_mode(self):
        """Test optimization trigger in manual mode."""
        self.coordinator.config.AUTOTUNE_ENABLED = False
        
        # Mock button not pressed
        with patch.object(self.coordinator.nt_interface, 'read_run_optimization_button', return_value=False):
            result = self.coordinator._check_optimization_trigger()
        
        self.assertFalse(result)
        
        # Mock button pressed
        with patch.object(self.coordinator.nt_interface, 'read_run_optimization_button', return_value=True):
            # Add some shots
            self.coordinator.accumulated_shots = [
                {'shot_data': Mock(), 'coefficient_values': {}}
            ]
            result = self.coordinator._check_optimization_trigger()
        
        self.assertTrue(result)
    
    def test_check_optimization_trigger_auto_mode(self):
        """Test optimization trigger in automatic mode."""
        self.coordinator.config.AUTOTUNE_ENABLED = True
        self.coordinator.config.AUTOTUNE_SHOT_THRESHOLD = 5
        
        # Not enough shots
        self.coordinator.accumulated_shots = [
            {'shot_data': Mock(), 'coefficient_values': {}}
            for _ in range(3)
        ]
        
        result = self.coordinator._check_optimization_trigger()
        self.assertFalse(result)
        
        # Enough shots
        self.coordinator.accumulated_shots = [
            {'shot_data': Mock(), 'coefficient_values': {}}
            for _ in range(5)
        ]
        
        result = self.coordinator._check_optimization_trigger()
        self.assertTrue(result)
    
    def test_run_optimization_clears_shots(self):
        """Test that running optimization clears accumulated shots."""
        # Add some real shot data instead of mocks
        shot_data = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        self.coordinator.accumulated_shots = [
            {
                'shot_data': shot_data,
                'coefficient_values': {'kDragCoefficient': 0.003}
            }
            for _ in range(5)
        ]
        
        # Mock optimizer and NT interface
        with patch.object(self.coordinator.optimizer, 'suggest_coefficient_update', return_value=('kDragCoefficient', 0.003)):
            with patch.object(self.coordinator.nt_interface, 'write_coefficient', return_value=True):
                self.coordinator._run_optimization()
        
        # Shots should be cleared
        self.assertEqual(len(self.coordinator.accumulated_shots), 0)
    
    def test_skip_to_next_coefficient(self):
        """Test skipping to next coefficient."""
        initial_index = self.coordinator.optimizer.current_index
        
        with patch.object(self.coordinator.optimizer, 'advance_to_next_coefficient') as mock_advance:
            self.coordinator._skip_to_next_coefficient()
            
            mock_advance.assert_called_once()
        
        # Accumulated shots should be cleared
        self.assertEqual(len(self.coordinator.accumulated_shots), 0)
    
    def test_update_status_writes_to_nt(self):
        """Test that status updates are written to NetworkTables."""
        with patch.object(self.coordinator.nt_interface, 'write_autotune_status') as mock_write:
            with patch.object(self.coordinator.optimizer, 'get_tuning_status', return_value='Tuning kDragCoefficient'):
                self.coordinator._update_status()
                
                # Should write status
                mock_write.assert_called()


class TestBayesianTunerCoordinatorHotkeys(unittest.TestCase):
    """Test hotkey functionality."""
    
    def test_coordinator_initializes_with_or_without_hotkeys(self):
        """Test that coordinator initializes regardless of hotkey availability."""
        config = TunerConfig()
        temp_dir = tempfile.mkdtemp()
        config.LOG_DIRECTORY = temp_dir
        
        # Should not raise error whether or not keyboard library is available
        coordinator = BayesianTunerCoordinator(config)
        self.assertIsNotNone(coordinator)
        
        # Clean up
        shutil.rmtree(temp_dir)


class TestBayesianTunerCoordinatorIntegration(unittest.TestCase):
    """Integration-style tests with mocked dependencies."""
    
    @patch('time.sleep')
    def test_full_lifecycle(self, mock_sleep):
        """Test full start-stop lifecycle."""
        config = TunerConfig()
        config.TUNER_ENABLED = True
        temp_dir = tempfile.mkdtemp()
        config.LOG_DIRECTORY = temp_dir
        
        coordinator = BayesianTunerCoordinator(config)
        
        # Mock NT interface
        with patch.object(coordinator.nt_interface, 'start', return_value=True):
            with patch.object(coordinator.nt_interface, 'read_all_coefficients', return_value={}):
                with patch.object(coordinator.nt_interface, 'write_interlock_settings'):
                    with patch.object(coordinator.nt_interface, 'write_autotune_status'):
                        with patch.object(coordinator.nt_interface, 'initialize_manual_controls'):
                            with patch.object(coordinator.nt_interface, 'initialize_fine_tuning_controls'):
                                with patch.object(coordinator.nt_interface, 'initialize_backtrack_controls'):
                                    # Start
                                    coordinator.start()
                                    
                                    # Verify running
                                    self.assertTrue(coordinator.running)
                                    self.assertIsNotNone(coordinator.thread)
                                    
                                    # Stop
                                    coordinator.stop()
                                    
                                    # Verify stopped
                                    self.assertFalse(coordinator.running)
                                    
                                    # Clean up
                                    shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
  
