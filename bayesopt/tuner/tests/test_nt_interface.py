"""
Unit tests for the NetworkTables interface module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TunerConfig
from nt_interface import NetworkTablesInterface, ShotData


class TestShotData(unittest.TestCase):
    """Test ShotData dataclass and validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
    
    def test_shot_data_creation(self):
        """Test creating a ShotData object."""
        shot = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        self.assertTrue(shot.hit)
        self.assertEqual(shot.distance, 5.0)
        self.assertEqual(shot.angle, 0.5)
        self.assertEqual(shot.velocity, 15.0)
    
    def test_shot_data_valid(self):
        """Test validation of valid shot data."""
        shot = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        self.assertTrue(shot.is_valid(self.config))
    
    def test_shot_data_invalid_distance(self):
        """Test validation with invalid distance."""
        # Negative distance
        shot = ShotData(
            hit=True,
            distance=-1.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        self.assertFalse(shot.is_valid(self.config))
        
        # Too far distance
        shot = ShotData(
            hit=True,
            distance=100.0,  # Exceeds max
            angle=0.5,
            velocity=15.0,
            timestamp=time.time()
        )
        
        self.assertFalse(shot.is_valid(self.config))
    
    def test_shot_data_invalid_velocity(self):
        """Test validation with invalid velocity."""
        # Negative velocity
        shot = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=-1.0,
            timestamp=time.time()
        )
        
        self.assertFalse(shot.is_valid(self.config))
        
        # Too high velocity
        shot = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=100.0,  # Exceeds max
            timestamp=time.time()
        )
        
        self.assertFalse(shot.is_valid(self.config))
    
    def test_shot_data_invalid_angle(self):
        """Test validation with invalid angle."""
        # Negative angle (below minimum)
        shot = ShotData(
            hit=True,
            distance=5.0,
            angle=-5.0,
            velocity=15.0,
            timestamp=time.time()
        )
        
        self.assertFalse(shot.is_valid(self.config))
        
        # Too high angle
        shot = ShotData(
            hit=True,
            distance=5.0,
            angle=10.0,  # Exceeds max
            velocity=15.0,
            timestamp=time.time()
        )
        
        self.assertFalse(shot.is_valid(self.config))
    
    def test_shot_data_with_extra_fields(self):
        """Test shot data with additional optional fields."""
        shot = ShotData(
            hit=True,
            distance=5.0,
            angle=0.5,
            velocity=15.0,
            timestamp=time.time(),
            yaw=0.1,
            target_height=2.64,
            launch_height=0.8,
            drag_coefficient=0.003,
            air_density=1.225,
            projectile_mass=0.27,
            projectile_area=0.04
        )
        
        self.assertTrue(shot.is_valid(self.config))
        self.assertEqual(shot.yaw, 0.1)
        self.assertEqual(shot.target_height, 2.64)
        self.assertEqual(shot.drag_coefficient, 0.003)


class TestNetworkTablesInterface(unittest.TestCase):
    """Test NetworkTablesInterface class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TunerConfig()
        self.interface = NetworkTablesInterface(self.config)
    
    def test_initialization(self):
        """Test interface initialization."""
        self.assertIsNotNone(self.interface.config)
        self.assertFalse(self.interface.connected)
        self.assertEqual(len(self.interface.pending_writes), 0)
        self.assertEqual(self.interface.last_shot_timestamp, 0.0)
    
    def test_rate_limiting_configuration(self):
        """Test that rate limiting is configured correctly."""
        self.assertGreater(self.interface.min_write_interval, 0)
        self.assertGreater(self.interface.min_read_interval, 0)
        
        # Verify it's based on config
        expected_write_interval = 1.0 / self.config.MAX_NT_WRITE_RATE_HZ
        expected_read_interval = 1.0 / self.config.MAX_NT_READ_RATE_HZ
        
        self.assertEqual(self.interface.min_write_interval, expected_write_interval)
        self.assertEqual(self.interface.min_read_interval, expected_read_interval)
    
    @patch('nt_interface.NetworkTables')
    def test_is_connected_when_disconnected(self, mock_nt):
        """Test is_connected when not connected."""
        mock_nt.isConnected.return_value = False
        
        self.assertFalse(self.interface.is_connected())
    
    @patch('nt_interface.NetworkTables')
    def test_is_connected_when_connected(self, mock_nt):
        """Test is_connected when connected."""
        mock_nt.isConnected.return_value = True
        self.interface.connected = True
        
        self.assertTrue(self.interface.is_connected())
    
    @patch('nt_interface.NetworkTables')
    def test_read_coefficient_when_disconnected(self, mock_nt):
        """Test reading coefficient when disconnected."""
        mock_nt.isConnected.return_value = False
        self.interface.connected = False
        
        default_value = 0.003
        result = self.interface.read_coefficient("/test", default_value)
        
        self.assertEqual(result, default_value)
    
    @patch('nt_interface.NetworkTables')
    def test_write_coefficient_when_disconnected(self, mock_nt):
        """Test writing coefficient when disconnected."""
        mock_nt.isConnected.return_value = False
        self.interface.connected = False
        
        result = self.interface.write_coefficient("/test", 0.003)
        
        self.assertFalse(result)
    
    @patch('nt_interface.NetworkTables')
    def test_write_coefficient_rate_limiting(self, mock_nt):
        """Test that write rate limiting works."""
        # Mock connection
        mock_nt.isConnected.return_value = True
        self.interface.connected = True
        
        # Mock table
        mock_table = Mock()
        self.interface.tuning_table = mock_table
        
        # First write should succeed
        result1 = self.interface.write_coefficient("/test", 0.003)
        self.assertTrue(result1)
        
        # Immediate second write should be rate limited (unless force=True)
        result2 = self.interface.write_coefficient("/test", 0.004)
        self.assertFalse(result2)
        
        # After waiting, write should succeed
        time.sleep(self.interface.min_write_interval + 0.01)
        result3 = self.interface.write_coefficient("/test", 0.005)
        self.assertTrue(result3)
    
    @patch('nt_interface.NetworkTables')
    def test_write_coefficient_force_bypass_rate_limit(self, mock_nt):
        """Test that force=True bypasses rate limiting."""
        # Mock connection
        mock_nt.isConnected.return_value = True
        self.interface.connected = True
        
        # Mock table
        mock_table = Mock()
        self.interface.tuning_table = mock_table
        
        # First write
        result1 = self.interface.write_coefficient("/test", 0.003)
        self.assertTrue(result1)
        
        # Immediate second write with force=True should succeed
        result2 = self.interface.write_coefficient("/test", 0.004, force=True)
        self.assertTrue(result2)
    
    @patch('nt_interface.NetworkTables')
    def test_pending_writes_accumulation(self, mock_nt):
        """Test that writes are queued when rate limited."""
        # Mock connection
        mock_nt.isConnected.return_value = True
        self.interface.connected = True
        self.config.NT_BATCH_WRITES = True
        
        # Mock table
        mock_table = Mock()
        self.interface.tuning_table = mock_table
        
        # First write should succeed
        self.interface.write_coefficient("/test1", 0.003)
        
        # Second immediate write should be queued
        self.interface.write_coefficient("/test2", 0.004)
        
        # Should have one pending write
        self.assertGreater(len(self.interface.pending_writes), 0)
    
    @patch('nt_interface.NetworkTables')
    def test_flush_pending_writes(self, mock_nt):
        """Test flushing pending writes."""
        # Mock connection
        mock_nt.isConnected.return_value = True
        self.interface.connected = True
        
        # Mock table
        mock_table = Mock()
        self.interface.tuning_table = mock_table
        
        # Add some pending writes manually
        self.interface.pending_writes["/test1"] = 0.003
        self.interface.pending_writes["/test2"] = 0.004
        
        # Flush
        count = self.interface.flush_pending_writes()
        
        self.assertEqual(count, 2)
        self.assertEqual(len(self.interface.pending_writes), 0)
    
    @patch('nt_interface.NetworkTables')
    def test_read_shot_data_when_disconnected(self, mock_nt):
        """Test reading shot data when disconnected."""
        mock_nt.isConnected.return_value = False
        self.interface.connected = False
        
        result = self.interface.read_shot_data()
        
        self.assertIsNone(result)
    
    @patch('nt_interface.NetworkTables')
    def test_read_shot_data_rate_limiting(self, mock_nt):
        """Test that shot data reading is rate limited."""
        # Mock connection
        mock_nt.isConnected.return_value = True
        self.interface.connected = True
        
        # Mock table
        mock_table = Mock()
        mock_table.getNumber = Mock(return_value=0.0)
        self.interface.firing_solver_table = mock_table
        
        # First read should attempt (though it may return None if no new data)
        self.interface.read_shot_data()
        first_read_time = self.interface.last_read_time
        
        # Immediate second read should be skipped due to rate limiting
        result = self.interface.read_shot_data()
        self.assertIsNone(result)
        
        # Read time should not have changed
        self.assertEqual(self.interface.last_read_time, first_read_time)
    
    @patch('nt_interface.NetworkTables')
    def test_read_shot_data_no_new_data(self, mock_nt):
        """Test reading shot data when timestamp hasn't changed."""
        # Mock connection
        mock_nt.isConnected.return_value = True
        self.interface.connected = True
        
        # Mock table with same timestamp
        mock_table = Mock()
        mock_table.getNumber = Mock(return_value=123.0)
        self.interface.firing_solver_table = mock_table
        self.interface.last_shot_timestamp = 123.0
        
        # Wait to bypass rate limiting
        time.sleep(self.interface.min_read_interval + 0.01)
        
        # Read should return None (no new data)
        result = self.interface.read_shot_data()
        self.assertIsNone(result)
    
    @patch('nt_interface.NetworkTables')
    def test_is_match_mode_when_disconnected(self, mock_nt):
        """Test match mode check when disconnected."""
        mock_nt.isConnected.return_value = False
        self.interface.connected = False
        
        result = self.interface.is_match_mode()
        
        self.assertFalse(result)
    
    def test_stop(self):
        """Test stopping the interface."""
        self.interface.connected = True
        self.interface.stop()
        
        self.assertFalse(self.interface.connected)


if __name__ == '__main__':
    unittest.main()
  
