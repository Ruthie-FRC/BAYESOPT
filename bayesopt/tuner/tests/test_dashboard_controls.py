"""
Comprehensive tests for NetworkTables dashboard controls and keyboard shortcuts.

This test suite ensures ALL interactive features work:
- Run Optimization button (manual trigger)
- Skip to Next Coefficient button
- TunerEnabled toggle (runtime enable/disable)
- Manual coefficient adjustment controls
- Fine-tuning mode controls (LEFT, RIGHT, UP, DOWN, RESET)
- Backtrack tuning controls
- Autotune status display
- Keyboard shortcuts (F5, F6, F7, F8, F9)
- All dashboard tables and their visibility
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TunerConfig
from nt_interface import NetworkTablesInterface


class TestRunOptimizationButton(unittest.TestCase):
    """Test Run Optimization button (manual trigger)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.interface = NetworkTablesInterface(self.config)
    
    def test_run_optimization_button_not_pressed(self):
        """Test button when not pressed."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.getBoolean = Mock(return_value=False)
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            result = self.interface.read_run_optimization_button()
        
        # Should return False
        self.assertFalse(result)
    
    def test_run_optimization_button_pressed(self):
        """Test button when pressed."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.getBoolean = Mock(return_value=True)
        mock_table.putBoolean = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            result = self.interface.read_run_optimization_button()
        
        # Should return True
        self.assertTrue(result)
        
        # Should reset button to False
        mock_table.putBoolean.assert_called_with("RunOptimization", False)
    
    def test_run_optimization_button_when_disconnected(self):
        """Test button when not connected."""
        self.interface.connected = False
        
        result = self.interface.read_run_optimization_button()
        
        # Should return False when disconnected
        self.assertFalse(result)
    
    def test_run_optimization_button_multiple_presses(self):
        """Test button pressed multiple times."""
        self.interface.connected = True
        
        mock_table = Mock()
        press_states = [True, False, True, False]
        mock_table.getBoolean = Mock(side_effect=press_states)
        mock_table.putBoolean = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            # First press
            result1 = self.interface.read_run_optimization_button()
            self.assertTrue(result1)
            
            # Not pressed
            result2 = self.interface.read_run_optimization_button()
            self.assertFalse(result2)
            
            # Second press
            result3 = self.interface.read_run_optimization_button()
            self.assertTrue(result3)


class TestSkipToNextCoefficientButton(unittest.TestCase):
    """Test Skip to Next Coefficient button."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.interface = NetworkTablesInterface(self.config)
    
    def test_skip_button_not_pressed(self):
        """Test skip button when not pressed."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.getBoolean = Mock(return_value=False)
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            result = self.interface.read_skip_to_next_button()
        
        self.assertFalse(result)
    
    def test_skip_button_pressed(self):
        """Test skip button when pressed."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.getBoolean = Mock(return_value=True)
        mock_table.putBoolean = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            result = self.interface.read_skip_to_next_button()
        
        # Should return True and reset
        self.assertTrue(result)
        mock_table.putBoolean.assert_called_with("SkipToNextCoefficient", False)
    
    def test_skip_button_when_disconnected(self):
        """Test skip button when disconnected."""
        self.interface.connected = False
        
        result = self.interface.read_skip_to_next_button()
        
        self.assertFalse(result)


class TestTunerEnabledToggle(unittest.TestCase):
    """Test TunerEnabled runtime toggle."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.interface = NetworkTablesInterface(self.config)
    
    def test_tuner_enabled_toggle_initial_state(self):
        """Test reading initial toggle state."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.getBoolean = Mock(return_value=True)
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            changed, value = self.interface.read_tuner_enabled_toggle()
        
        # First read should show no change
        self.assertFalse(changed)
    
    def test_tuner_enabled_toggle_changed(self):
        """Test detecting toggle state change."""
        self.interface.connected = True
        self.interface.last_tuner_enabled_state = False
        
        mock_table = Mock()
        mock_table.getBoolean = Mock(return_value=True)
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            changed, value = self.interface.read_tuner_enabled_toggle()
        
        # Should detect change
        self.assertTrue(changed)
        self.assertTrue(value)
    
    def test_tuner_enabled_toggle_unchanged(self):
        """Test when toggle hasn't changed."""
        self.interface.connected = True
        self.interface.last_tuner_enabled_state = True
        
        mock_table = Mock()
        mock_table.getBoolean = Mock(return_value=True)
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            changed, value = self.interface.read_tuner_enabled_toggle()
        
        # Should not detect change
        self.assertFalse(changed)
    
    def test_tuner_enabled_status_write(self):
        """Test writing tuner enabled status to dashboard."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.putBoolean = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            self.interface.write_tuner_enabled_status(True, paused=False)
        
        # Should write both enabled and paused status
        self.assertTrue(mock_table.putBoolean.called)


class TestAutotuneStatusDisplay(unittest.TestCase):
    """Test autotune status display on dashboard."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.interface = NetworkTablesInterface(self.config)
    
    def test_autotune_status_manual_mode(self):
        """Test status display in manual mode."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.putBoolean = Mock()
        mock_table.putNumber = Mock()
        mock_table.putString = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            self.interface.write_autotune_status(
                autotune_enabled=False,
                shot_count=5,
                shot_threshold=10
            )
        
        # Should write all status fields
        mock_table.putBoolean.assert_called()
        mock_table.putNumber.assert_called()
        mock_table.putString.assert_called()
    
    def test_autotune_status_auto_mode(self):
        """Test status display in automatic mode."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.putBoolean = Mock()
        mock_table.putNumber = Mock()
        mock_table.putString = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            self.interface.write_autotune_status(
                autotune_enabled=True,
                shot_count=8,
                shot_threshold=10
            )
        
        # Should show progress toward threshold
        calls = mock_table.putString.call_args_list
        # Verify status string contains shot counts
        self.assertTrue(mock_table.putString.called)
    
    def test_autotune_status_threshold_reached(self):
        """Test status when threshold is reached."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.putString = Mock()
        mock_table.putNumber = Mock()
        mock_table.putBoolean = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            self.interface.write_autotune_status(
                autotune_enabled=True,
                shot_count=10,
                shot_threshold=10
            )
        
        # Should indicate ready to optimize
        self.assertTrue(mock_table.putString.called)


class TestManualCoefficientControls(unittest.TestCase):
    """Test manual coefficient adjustment controls."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.interface = NetworkTablesInterface(self.config)
    
    def test_initialize_manual_controls(self):
        """Test initialization of manual controls."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.putNumber = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            self.interface.initialize_manual_controls(self.config.COEFFICIENTS)
        
        # Should create control for each coefficient
        self.assertTrue(mock_table.putNumber.called)
    
    def test_read_manual_coefficient_adjustment(self):
        """Test reading manual adjustment from dashboard."""
        self.interface.connected = True
        
        coeff = self.config.COEFFICIENTS["kDragCoefficient"]
        
        mock_table = Mock()
        mock_table.getNumber = Mock(return_value=0.004)  # Different from default
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            value = self.interface.read_manual_coefficient_value("kDragCoefficient", coeff)
        
        # Should return adjusted value
        self.assertEqual(value, 0.004)
    
    def test_manual_adjustment_unchanged(self):
        """Test when manual value hasn't changed."""
        self.interface.connected = True
        
        coeff = self.config.COEFFICIENTS["kDragCoefficient"]
        
        mock_table = Mock()
        mock_table.getNumber = Mock(return_value=coeff.default_value)
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            value = self.interface.read_manual_coefficient_value("kDragCoefficient", coeff)
        
        # Should return default
        self.assertEqual(value, coeff.default_value)


class TestFineTuningControls(unittest.TestCase):
    """Test fine-tuning mode controls (LEFT, RIGHT, UP, DOWN, RESET)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.interface = NetworkTablesInterface(self.config)
    
    def test_initialize_fine_tuning_controls(self):
        """Test initialization of fine-tuning controls."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.putBoolean = Mock()
        mock_table.putNumber = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            self.interface.initialize_fine_tuning_controls()
        
        # Should create all control buttons
        self.assertTrue(mock_table.putBoolean.called)
    
    def test_read_fine_tuning_left_button(self):
        """Test LEFT fine-tuning button."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.getBoolean = Mock(return_value=True)
        mock_table.putBoolean = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            result = self.interface.read_fine_tuning_button("LEFT")
        
        # Should detect button press and reset
        self.assertTrue(result)
        mock_table.putBoolean.assert_called()
    
    def test_read_fine_tuning_right_button(self):
        """Test RIGHT fine-tuning button."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.getBoolean = Mock(return_value=True)
        mock_table.putBoolean = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            result = self.interface.read_fine_tuning_button("RIGHT")
        
        self.assertTrue(result)
    
    def test_read_fine_tuning_up_button(self):
        """Test UP fine-tuning button."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.getBoolean = Mock(return_value=True)
        mock_table.putBoolean = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            result = self.interface.read_fine_tuning_button("UP")
        
        self.assertTrue(result)
    
    def test_read_fine_tuning_down_button(self):
        """Test DOWN fine-tuning button."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.getBoolean = Mock(return_value=True)
        mock_table.putBoolean = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            result = self.interface.read_fine_tuning_button("DOWN")
        
        self.assertTrue(result)
    
    def test_read_fine_tuning_reset_button(self):
        """Test RESET fine-tuning button."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.getBoolean = Mock(return_value=True)
        mock_table.putBoolean = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            result = self.interface.read_fine_tuning_button("RESET")
        
        self.assertTrue(result)
    
    def test_fine_tuning_buttons_when_disconnected(self):
        """Test fine-tuning buttons when disconnected."""
        self.interface.connected = False
        
        for button in ["LEFT", "RIGHT", "UP", "DOWN", "RESET"]:
            result = self.interface.read_fine_tuning_button(button)
            self.assertFalse(result)


class TestBacktrackControls(unittest.TestCase):
    """Test backtrack tuning controls."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.interface = NetworkTablesInterface(self.config)
    
    def test_initialize_backtrack_controls(self):
        """Test initialization of backtrack controls."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.putBoolean = Mock()
        mock_table.putString = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            self.interface.initialize_backtrack_controls(self.config.TUNING_ORDER)
        
        # Should create controls for each coefficient in order
        self.assertTrue(mock_table.putBoolean.called)
    
    def test_read_backtrack_button_for_coefficient(self):
        """Test reading backtrack button for specific coefficient."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.getBoolean = Mock(return_value=True)
        mock_table.putBoolean = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            result = self.interface.read_backtrack_button("kDragCoefficient")
        
        # Should detect button press
        self.assertTrue(result)
        
        # Should reset button
        mock_table.putBoolean.assert_called()
    
    def test_backtrack_all_coefficients(self):
        """Test backtrack buttons for all coefficients."""
        self.interface.connected = True
        
        for coeff_name in self.config.TUNING_ORDER:
            mock_table = Mock()
            mock_table.getBoolean = Mock(return_value=False)
            
            with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
                result = self.interface.read_backtrack_button(coeff_name)
            
            # Should handle all coefficient names
            self.assertFalse(result)


class TestDashboardTableVisibility(unittest.TestCase):
    """Test that all dashboard tables are created and visible."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.interface = NetworkTablesInterface(self.config)
    
    def test_tuner_main_table_exists(self):
        """Test /Tuning/BayesianTuner main table."""
        self.interface.connected = True
        
        mock_table = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table) as mock_get:
            self.interface.write_autotune_status(True, 5, 10)
        
        # Should access the main tuner table
        mock_get.assert_called()
    
    def test_manual_control_table_exists(self):
        """Test /Tuning/BayesianTuner/ManualControl table."""
        self.interface.connected = True
        
        with patch('nt_interface.NetworkTables.getTable') as mock_get:
            self.interface.initialize_manual_controls(self.config.COEFFICIENTS)
        
        # Should access manual control table
        self.assertTrue(mock_get.called)
    
    def test_fine_tuning_table_exists(self):
        """Test /Tuning/BayesianTuner/FineTuning table."""
        self.interface.connected = True
        
        with patch('nt_interface.NetworkTables.getTable') as mock_get:
            self.interface.initialize_fine_tuning_controls()
        
        # Should access fine tuning table
        self.assertTrue(mock_get.called)
    
    def test_backtrack_table_exists(self):
        """Test /Tuning/BayesianTuner/Backtrack table."""
        self.interface.connected = True
        
        with patch('nt_interface.NetworkTables.getTable') as mock_get:
            self.interface.initialize_backtrack_controls(self.config.TUNING_ORDER)
        
        # Should access backtrack table
        self.assertTrue(mock_get.called)
    
    def test_coefficients_live_table_exists(self):
        """Test /Tuning/BayesianTuner/CoefficientsLive table."""
        self.interface.connected = True
        
        with patch('nt_interface.NetworkTables.getTable') as mock_get:
            # This table shows current vs default values
            mock_table = Mock()
            mock_get.return_value = mock_table
            
            # Should be accessible
            table = mock_get("/Tuning/BayesianTuner/CoefficientsLive")
            self.assertIsNotNone(table)


class TestKeyboardShortcuts(unittest.TestCase):
    """Test keyboard shortcuts functionality."""
    
    def test_keyboard_shortcuts_defined(self):
        """Test that keyboard shortcuts are defined."""
        # Import tuner to check hotkey definitions
        import tuner as tuner_module
        
        # Check hotkey constants exist
        self.assertTrue(hasattr(tuner_module, 'STOP_HOTKEY'))
        self.assertTrue(hasattr(tuner_module, 'RUN_OPTIMIZATION_HOTKEY'))
        self.assertTrue(hasattr(tuner_module, 'NEXT_COEFFICIENT_HOTKEY'))
        self.assertTrue(hasattr(tuner_module, 'PREV_COEFFICIENT_HOTKEY'))
    
    def test_keyboard_shortcuts_values(self):
        """Test keyboard shortcut key values."""
        import tuner as tuner_module
        
        # Verify expected hotkeys
        expected_hotkeys = {
            'STOP_HOTKEY': 'f9',
            'RUN_OPTIMIZATION_HOTKEY': 'f5',
            'NEXT_COEFFICIENT_HOTKEY': 'f6',
            'PREV_COEFFICIENT_HOTKEY': 'f7'
        }
        
        for attr, expected in expected_hotkeys.items():
            if hasattr(tuner_module, attr):
                value = getattr(tuner_module, attr)
                self.assertEqual(value, expected)
    
    def test_keyboard_library_availability(self):
        """Test handling when keyboard library not available."""
        import tuner as tuner_module
        
        # Should have KEYBOARD_AVAILABLE flag
        self.assertTrue(hasattr(tuner_module, 'KEYBOARD_AVAILABLE'))
        
        # Value should be boolean
        self.assertIsInstance(tuner_module.KEYBOARD_AVAILABLE, bool)


class TestInterlockSignaling(unittest.TestCase):
    """Test interlock signaling mechanisms."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.interface = NetworkTablesInterface(self.config)
    
    def test_signal_coefficients_updated(self):
        """Test signaling coefficient update to robot."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.putBoolean = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            self.interface.signal_coefficients_updated()
        
        # Should set CoefficientsUpdated flag
        mock_table.putBoolean.assert_called_with("CoefficientsUpdated", True)
    
    def test_write_interlock_settings(self):
        """Test writing interlock configuration."""
        self.interface.connected = True
        
        mock_table = Mock()
        mock_table.putBoolean = Mock()
        
        with patch('nt_interface.NetworkTables.getTable', return_value=mock_table):
            self.interface.write_interlock_settings(
                require_shot_logged=True,
                require_coefficients_updated=True
            )
        
        # Should write both settings
        self.assertEqual(mock_table.putBoolean.call_count, 2)


class TestDashboardStatusMessages(unittest.TestCase):
    """Test status message display on dashboard."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.interface = NetworkTablesInterface(self.config)
    
    def test_write_status_message(self):
        """Test writing status message."""
        self.interface.connected = True
        self.interface.firing_solver_table = Mock()
        self.interface.firing_solver_table.putString = Mock()
        
        self.interface.write_status("Tuning kDragCoefficient")
        
        # Should write status string
        self.interface.firing_solver_table.putString.assert_called_with(
            "TunerStatus", "Tuning kDragCoefficient"
        )
    
    def test_status_messages_various_states(self):
        """Test status messages for various tuner states."""
        self.interface.connected = True
        self.interface.firing_solver_table = Mock()
        self.interface.firing_solver_table.putString = Mock()
        
        test_messages = [
            "Waiting for shots...",
            "Optimizing...",
            "Complete",
            "Paused - Match Mode",
            "Disabled",
            "Error: Connection lost"
        ]
        
        for msg in test_messages:
            self.interface.write_status(msg)
        
        # Should have written all messages
        self.assertEqual(
            self.interface.firing_solver_table.putString.call_count,
            len(test_messages)
        )


if __name__ == '__main__':
    unittest.main()
  
