"""
NetworkTables interface module for the Bayesian Tuner.

This module handles all NetworkTables communication including:
- Reading shot data and match mode status
- Writing updated coefficient values
- Connection management and error handling
- Status feedback to drivers
"""

import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

try:
    from networktables import NetworkTables
except ImportError:
    # Provide a mock for testing without pynetworktables
    class NetworkTables:
        @staticmethod
        def initialize(server=None):
            pass
        
        @staticmethod
        def isConnected():
            return False
        
        @staticmethod
        def getTable(name):
            return None


logger = logging.getLogger(__name__)


@dataclass
class ShotData:
    """Container for shot data from NetworkTables."""
    
    hit: bool
    distance: float
    angle: float
    velocity: float
    timestamp: float
    
    # Additional data captured at shot time
    yaw: float = 0.0  # Turret yaw angle
    target_height: float = 0.0  # Target height used
    launch_height: float = 0.0  # Launch height used
    
    # Current coefficient values at time of shot
    drag_coefficient: float = 0.0
    air_density: float = 0.0
    projectile_mass: float = 0.0
    projectile_area: float = 0.0
    
    def is_valid(self, config) -> bool:
        """
        Check if shot data is valid and within physical limits.
        
        Args:
            config: TunerConfig with physical limit constants
            
        Returns:
            True if shot data is valid and physically reasonable
        """
        return (
            isinstance(self.hit, bool)
            and isinstance(self.distance, (int, float))
            and isinstance(self.angle, (int, float))
            and isinstance(self.velocity, (int, float))
            # Distance bounds check (field geometry)
            and config.PHYSICAL_MIN_DISTANCE_M <= self.distance <= config.PHYSICAL_MAX_DISTANCE_M
            # Velocity bounds check (motor/mechanism physical limits)
            and config.PHYSICAL_MIN_VELOCITY_MPS <= self.velocity <= config.PHYSICAL_MAX_VELOCITY_MPS
            # Angle bounds check (mechanism physical limits)
            and config.PHYSICAL_MIN_ANGLE_RAD <= self.angle <= config.PHYSICAL_MAX_ANGLE_RAD
        )

class NetworkTablesInterface:
    """Interface for NetworkTables communication with RoboRIO protection."""
    
    def __init__(self, config):
        """
        Initialize NetworkTables interface with rate limiting.
        
        Args:
            config: TunerConfig instance with NT settings and rate limits
        """
        self.config = config
        self.connected = False
        self.last_connection_attempt = 0.0
        self.shot_data_listeners = []
        
        # Rate limiting to prevent RoboRIO overload
        self.last_write_time = 0.0
        self.min_write_interval = 1.0 / config.MAX_NT_WRITE_RATE_HZ
        self.last_read_time = 0.0
        self.min_read_interval = 1.0 / config.MAX_NT_READ_RATE_HZ
        self.pending_writes = {}  # For batching writes if enabled
        
        # Tables
        self.root_table = None
        self.tuning_table = None
        self.firing_solver_table = None
        
        # Last shot data
        self.last_shot_timestamp = 0.0
        self.last_shot_data: Optional[ShotData] = None
        
        logger.info("NetworkTables interface initialized with rate limiting")
        logger.info(f"Write rate limit: {config.MAX_NT_WRITE_RATE_HZ} Hz, "
                   f"Read rate limit: {config.MAX_NT_READ_RATE_HZ} Hz")
    
    def connect(self, server_ip: Optional[str] = None) -> bool:
        """
        Connect to NetworkTables server.
        
        Args:
            server_ip: IP address of robot/server. If None, uses config default.
        
        Returns:
            True if connected successfully, False otherwise
        """
        current_time = time.time()
        
        # Throttle connection attempts
        if current_time - self.last_connection_attempt < self.config.NT_RECONNECT_DELAY_SECONDS:
            return self.connected
        
        self.last_connection_attempt = current_time
        
        try:
            if server_ip is None:
                server_ip = self.config.NT_SERVER_IP
            
            logger.info(f"Attempting to connect to NetworkTables at {server_ip}")
            NetworkTables.initialize(server=server_ip)
            
            # Wait for connection
            timeout = self.config.NT_TIMEOUT_SECONDS
            start_time = time.time()
            
            while not NetworkTables.isConnected():
                if time.time() - start_time > timeout:
                    logger.warning(f"Connection timeout after {timeout}s")
                    return False
                time.sleep(0.1)
            
            # Get tables
            self.root_table = NetworkTables.getTable("")
            self.tuning_table = NetworkTables.getTable("/Tuning")
            self.firing_solver_table = NetworkTables.getTable(self.config.NT_SHOT_DATA_TABLE)
            
            self.connected = True
            logger.info("Connected to NetworkTables successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to NetworkTables: {e}")
            self.connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to NetworkTables."""
        try:
            self.connected = NetworkTables.isConnected()
        except Exception as e:
            logger.error(f"Error checking connection status: {e}")
            self.connected = False
        
        return self.connected
    
    def disconnect(self):
        """Disconnect from NetworkTables."""
        try:
            # NetworkTables doesn't have an explicit disconnect in pynetworktables
            self.connected = False
            logger.info("Disconnected from NetworkTables")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def read_coefficient(self, nt_key: str, default_value: float) -> float:
        """
        Read a coefficient value from NetworkTables.
        
        Args:
            nt_key: NetworkTables key path
            default_value: Default value if key doesn't exist
        
        Returns:
            Current coefficient value
        """
        if not self.is_connected():
            logger.warning(f"Not connected, returning default for {nt_key}")
            return default_value
        
        try:
            value = self.tuning_table.getNumber(nt_key, default_value)
            return value
        except Exception as e:
            logger.error(f"Error reading {nt_key}: {e}")
            return default_value
    
    def write_coefficient(self, nt_key: str, value: float, force: bool = False) -> bool:
        """
        Write a coefficient value to NetworkTables with rate limiting.
        
        Protects RoboRIO from being overloaded with too frequent updates.
        
        Args:
            nt_key: NetworkTables key path
            value: Coefficient value to write
            force: If True, bypass rate limiting (use sparingly)
        
        Returns:
            True if write succeeded, False otherwise
        """
        if not self.is_connected():
            logger.warning(f"Not connected, cannot write {nt_key}")
            return False
        
        # Rate limiting check (unless forced)
        current_time = time.time()
        if not force:
            time_since_last_write = current_time - self.last_write_time
            if time_since_last_write < self.min_write_interval:
                # Too soon, queue for batching if enabled
                if self.config.NT_BATCH_WRITES:
                    self.pending_writes[nt_key] = value
                    logger.debug(f"Queueing write for {nt_key} due to rate limit")
                    return False
                else:
                    logger.debug(f"Skipping write for {nt_key} due to rate limit")
                    return False
        
        try:
            self.tuning_table.putNumber(nt_key, value)
            self.last_write_time = current_time
            logger.info(f"Wrote {nt_key} = {value}")
            return True
        except Exception as e:
            logger.error(f"Error writing {nt_key}: {e}")
            return False
    
    def flush_pending_writes(self) -> int:
        """
        Flush any pending batched writes to NetworkTables.
        
        Returns:
            Number of writes flushed
        """
        if not self.pending_writes:
            return 0
        
        count = 0
        for nt_key, value in list(self.pending_writes.items()):
            if self.write_coefficient(nt_key, value, force=True):
                count += 1
                del self.pending_writes[nt_key]
        
        if count > 0:
            logger.info(f"Flushed {count} batched writes to NetworkTables")
        
        return count
    
    def read_shot_data(self) -> Optional[ShotData]:
        """
        Read the latest shot data from NetworkTables with rate limiting.
        
        Protects RoboRIO from excessive read requests.
        Captures ALL robot state data at the moment of the shot including:
        - Shot result (hit/miss)
        - Calculated firing solution (distance, angle, velocity, yaw)
        - Physical parameters (target height, launch height)
        - Current coefficient values being used
        
        Returns:
            ShotData object if new data available, None otherwise
        """
        if not self.is_connected():
            return None
        
        # Rate limiting check
        current_time = time.time()
        time_since_last_read = current_time - self.last_read_time
        if time_since_last_read < self.min_read_interval:
            return None  # Skip read to avoid overloading RoboRIO
        
        self.last_read_time = current_time
        
        try:
            # Check if there's new shot data by monitoring timestamp
            shot_timestamp = self.firing_solver_table.getNumber("ShotTimestamp", 0.0)
            
            # Only process if this is a new shot
            if shot_timestamp <= self.last_shot_timestamp:
                return None
            
            # Read shot result (hit or miss)
            hit = self.firing_solver_table.getBoolean("Hit", False)
            
            # Read calculated firing solution data
            distance = self.firing_solver_table.getNumber("Distance", 0.0)
            
            # Read from solution subtable
            solution_table = self.firing_solver_table.getSubTable("Solution")
            angle = solution_table.getNumber("pitchRadians", 0.0)
            velocity = solution_table.getNumber("exitVelocity", 0.0)
            yaw = solution_table.getNumber("yawRadians", 0.0)
            
            # Read physical parameters used in calculation
            target_height = self.firing_solver_table.getNumber("TargetHeight", 0.0)
            launch_height = self.firing_solver_table.getNumber("LaunchHeight", 0.0)
            
            # Read current coefficient values AT TIME OF SHOT
            drag_coeff = self.firing_solver_table.getNumber("DragCoefficient", 0.0)
            air_density = self.firing_solver_table.getNumber("AirDensity", 1.225)
            projectile_mass = self.firing_solver_table.getNumber("ProjectileMass", 0.0)
            projectile_area = self.firing_solver_table.getNumber("ProjectileArea", 0.0)
            
            # Create comprehensive shot data object
            shot_data = ShotData(
                hit=hit,
                distance=distance,
                angle=angle,
                velocity=velocity,
                timestamp=current_timestamp,
                yaw=yaw,
                target_height=target_height,
                launch_height=launch_height,
                drag_coefficient=drag_coeff,
                air_density=air_density,
                projectile_mass=projectile_mass,
                projectile_area=projectile_area,
            )
            
            # Update tracking
            self.last_shot_timestamp = shot_timestamp
            self.last_shot_data = shot_data
            
            logger.info(f"New shot captured: hit={hit}, dist={distance:.2f}m, "
                       f"angle={angle:.3f}rad, vel={velocity:.2f}m/s, "
                       f"drag={drag_coeff:.6f}")
            
            return shot_data
            
        except Exception as e:
            logger.error(f"Error reading shot data: {e}")
            return None
    
    def is_match_mode(self) -> bool:
        """
        Check if robot is in match mode (FMS attached).
        
        Returns:
            True if in match mode, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Check FMSInfo for FMS control data
            fms_table = NetworkTables.getTable("/FMSInfo")
            
            # If FMSControlData exists and is not 0, we're in a match
            fms_control = fms_table.getNumber("FMSControlData", 0)
            return fms_control != 0
            
        except Exception as e:
            logger.error(f"Error checking match mode: {e}")
            return False
    
    def write_status(self, status: str):
        """
        Write tuner status message to NetworkTables for driver feedback.
        
        Args:
            status: Status message string
        """
        if not self.is_connected():
            return
        
        try:
            self.firing_solver_table.putString("TunerStatus", status)
            logger.debug(f"Status: {status}")
        except Exception as e:
            logger.error(f"Error writing status: {e}")
    
    def read_all_coefficients(self, coefficients: Dict[str, Any]) -> Dict[str, float]:
        """
        Read all coefficient values from NetworkTables.
        
        Args:
            coefficients: Dict of CoefficientConfig objects
        
        Returns:
            Dict mapping coefficient names to current values
        """
        values = {}
        for name, coeff in coefficients.items():
            values[name] = self.read_coefficient(coeff.nt_key, coeff.default_value)
        
        return values
    
    def write_all_coefficients(self, coefficient_values: Dict[str, float]) -> bool:
        """
        Write multiple coefficient values to NetworkTables.
        
        Args:
            coefficient_values: Dict mapping coefficient names to values
        
        Returns:
            True if all writes succeeded, False otherwise
        """
        success = True
        for name, value in coefficient_values.items():
            if name in self.config.COEFFICIENTS:
                coeff = self.config.COEFFICIENTS[name]
                if not self.write_coefficient(coeff.nt_key, value):
                    success = False
        
        return success
    
    def write_interlock_settings(self, require_shot_logged: bool, require_coefficients_updated: bool):
        """
        Write shooting interlock settings to NetworkTables.
        
        Args:
            require_shot_logged: If True, robot must wait for shot to be logged
            require_coefficients_updated: If True, robot must wait for coefficient update
        """
        if not self.is_connected():
            return
        
        try:
            interlock_table = NetworkTables.getTable("/FiringSolver/Interlock")
            interlock_table.putBoolean("RequireShotLogged", require_shot_logged)
            interlock_table.putBoolean("RequireCoefficientsUpdated", require_coefficients_updated)
            
            logger.info(f"Interlock settings: shot_logged={require_shot_logged}, coeff_updated={require_coefficients_updated}")
        except Exception as e:
            logger.error(f"Error writing interlock settings: {e}")
    
    def signal_coefficients_updated(self):
        """
        Signal that coefficients have been updated (clears interlock).
        
        Sets the CoefficientsUpdated flag to true, allowing robot to shoot
        if that interlock is enabled.
        """
        if not self.is_connected():
            return
        
        try:
            interlock_table = NetworkTables.getTable("/FiringSolver/Interlock")
            interlock_table.putBoolean("CoefficientsUpdated", True)
            logger.debug("Signaled coefficients updated")
        except Exception as e:
            logger.error(f"Error signaling coefficient update: {e}")
