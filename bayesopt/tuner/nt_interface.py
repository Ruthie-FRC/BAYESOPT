"""
NetworkTables interface module for the Bayesian Tuner.

This module handles all NetworkTables communication including:
- Reading shot data and match mode status
- Writing updated coefficient values
- Connection management and error handling
- Status feedback to drivers
- Dashboard controls for autotune feature (button and status display)
- Manual coefficient adjustment from dashboard (for real-time tuning)
- Fine-tuning mode controls (closer/farther from target center)

Dashboard Controls Published:
-----------------------------
The tuner publishes the following to /Tuning/BayesianTuner:
    - RunOptimization (bool): Button for manual optimization trigger
    - AutotuneEnabled (bool): Shows current autotune mode
    - ShotCount (int): Number of accumulated shots
    - ShotThreshold (int): Target shots before auto-optimization
    - TunerEnabled (bool): Toggle to enable/disable tuner at runtime
    
Manual Coefficient Control (at /Tuning/BayesianTuner/ManualControl/):
    - ManualAdjustEnabled (bool): Enable manual coefficient adjustment
    - CoefficientName (string): Which coefficient to adjust
    - NewValue (number): New value to set
    - ApplyManualValue (bool): Button to apply the manual value
    
Fine-Tuning Mode (at /Tuning/BayesianTuner/FineTuning/):
    - FineTuningEnabled (bool): Enable fine-tuning mode
    - TargetBias (string): "CENTER", "LEFT", "RIGHT", "UP", "DOWN"
    - BiasAmount (number): How much to bias (0.0-1.0)
    
Backtrack Tuning (at /Tuning/BayesianTuner/Backtrack/):
    - BacktrackEnabled (bool): Allow tuner to go back to previous coefficients
    - BacktrackToCoefficient (string): Name of coefficient to backtrack to
    - TriggerBacktrack (bool): Button to trigger backtrack

When autotune_enabled = False:
    Drivers can press the "RunOptimization" button on the dashboard
    (displayed in Shuffleboard/SmartDashboard) to trigger coefficient
    optimization using the accumulated shot data.

When autotune_enabled = True:
    The tuner automatically runs optimization when ShotCount reaches
    ShotThreshold. The dashboard shows progress toward this threshold.
"""

import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

try:
    # Try pyntcore first (modern WPILib 2024+)
    import ntcore
    
    class NetworkTables:
        """Wrapper to provide pynetworktables-like API for pyntcore."""
        _inst = None
        
        @staticmethod
        def initialize(server=None):
            NetworkTables._inst = ntcore.NetworkTableInstance.getDefault()
            if server:
                NetworkTables._inst.setServer(server)
            NetworkTables._inst.startClient4("BayesOptTuner")
        
        @staticmethod
        def isConnected():
            if NetworkTables._inst is None:
                return False
            return NetworkTables._inst.isConnected()
        
        @staticmethod
        def getTable(name):
            if NetworkTables._inst is None:
                return None
            return NetworkTables._inst.getTable(name)
    
except ImportError:
    try:
        # Fall back to pynetworktables (older API)
        from networktables import NetworkTables
    except ImportError:
        # Provide a mock for testing without any NetworkTables library
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
    
    def start(self, server_ip: Optional[str] = None) -> bool:
        """
        Start NetworkTables connection.
        
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
    
    def connect(self, server_ip: Optional[str] = None) -> bool:
        """
        Connect to NetworkTables server.
        
        Deprecated: Use start() instead for API consistency.
        
        Args:
            server_ip: IP address of robot/server. If None, uses config default.
        
        Returns:
            True if connected successfully, False otherwise
        """
        return self.start(server_ip)
    
    def is_connected(self) -> bool:
        """Check if connected to NetworkTables."""
        try:
            self.connected = NetworkTables.isConnected()
        except Exception as e:
            logger.error(f"Error checking connection status: {e}")
            self.connected = False
        
        return self.connected
    
    def stop(self):
        """Stop NetworkTables connection."""
        try:
            # NetworkTables doesn't have an explicit stop in pynetworktables
            self.connected = False
            logger.info("Stopped NetworkTables connection")
        except Exception as e:
            logger.error(f"Error during stop: {e}")
    
    def disconnect(self):
        """
        Disconnect from NetworkTables.
        
        Deprecated: Use stop() instead for API consistency.
        """
        self.stop()
    
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
                timestamp=shot_timestamp,
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
    
    def read_run_optimization_button(self) -> bool:
        """
        Read the "Run Optimization" button state from the dashboard.
        
        This is the MANUAL TRIGGER for optimization when autotune is disabled.
        
        How it works:
        1. The tuner publishes a "RunOptimization" boolean to NetworkTables
        2. This appears as a toggleable button in Shuffleboard/SmartDashboard
        3. When the driver clicks the button, it sets the value to True
        4. This method reads that value, and if True:
           - Returns True to trigger optimization
           - Resets the button to False so it doesn't trigger again
        
        Dashboard Location: /Tuning/BayesianTuner/RunOptimization
        
        Returns:
            True if the button was pressed (also resets the button state to False)
            False if button not pressed or not connected
        """
        if not self.is_connected():
            return False
        
        try:
            # Read from the BayesianTuner table where dashboard controls live
            tuner_table = NetworkTables.getTable("/Tuning/BayesianTuner")
            button_pressed = tuner_table.getBoolean("RunOptimization", False)
            
            if button_pressed:
                # Reset the button state so it doesn't trigger again
                # This makes it a "one-shot" button - press once, runs once
                tuner_table.putBoolean("RunOptimization", False)
                logger.info("Run Optimization button pressed - triggering manual optimization")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error reading run optimization button: {e}")
            return False
    
    def write_autotune_status(self, autotune_enabled: bool, shot_count: int, shot_threshold: int):
        """
        Write autotune status to NetworkTables for dashboard display.
        
        This publishes information to the dashboard so drivers can see:
        - Whether autotune is enabled or in manual mode
        - How many shots have been accumulated
        - How many shots are needed before auto-optimization runs
        
        Also initializes the "Run Optimization" button if it doesn't exist,
        so it appears on the dashboard for manual triggering.
        
        Dashboard Location: /Tuning/BayesianTuner/
        Published Values:
            - AutotuneEnabled (bool): Current mode
            - ShotCount (int): Accumulated shots so far
            - ShotThreshold (int): Target for auto-optimization
            - RunOptimization (bool): Button for manual trigger (initialized to False)
        
        Args:
            autotune_enabled: Whether autotune mode is enabled
            shot_count: Current number of accumulated shots
            shot_threshold: Number of shots required before auto-optimization
        """
        if not self.is_connected():
            return
        
        try:
            tuner_table = NetworkTables.getTable("/Tuning/BayesianTuner")
            tuner_table.putBoolean("AutotuneEnabled", autotune_enabled)
            tuner_table.putNumber("ShotCount", shot_count)
            tuner_table.putNumber("ShotThreshold", shot_threshold)
            
            # Show/hide the RunOptimization button based on autotune mode
            # Button should only appear when in manual mode (autotune disabled)
            if not autotune_enabled:
                # Initialize the button if it doesn't exist (manual mode)
                if not tuner_table.containsKey("RunOptimization"):
                    tuner_table.putBoolean("RunOptimization", False)
            
            # Initialize SkipToNextCoefficient button if it doesn't exist
            if not tuner_table.containsKey("SkipToNextCoefficient"):
                tuner_table.putBoolean("SkipToNextCoefficient", False)
            
            # ── GLOBAL Sample Size Adjustment ──
            # Input field for new global threshold value
            if not tuner_table.containsKey("NewGlobalThreshold"):
                tuner_table.putNumber("NewGlobalThreshold", shot_threshold)
            # Button to apply the new global threshold
            if not tuner_table.containsKey("UpdateGlobalThreshold"):
                tuner_table.putBoolean("UpdateGlobalThreshold", False)
            
            # ── LOCAL (per-coefficient) Sample Size Adjustment ──
            # Input field for new local threshold value (for current coefficient only)
            if not tuner_table.containsKey("NewLocalThreshold"):
                tuner_table.putNumber("NewLocalThreshold", shot_threshold)
            # Button to apply the new local threshold
            if not tuner_table.containsKey("UpdateLocalThreshold"):
                tuner_table.putBoolean("UpdateLocalThreshold", False)
            
            logger.debug(f"Autotune status: enabled={autotune_enabled}, shots={shot_count}/{shot_threshold}")
        except Exception as e:
            logger.error(f"Error writing autotune status: {e}")
    
    def read_skip_to_next_button(self) -> bool:
        """
        Read the "Skip to Next Coefficient" button state from the dashboard.
        
        When pressed, the tuner will move to tuning the next coefficient
        in the TUNING_ORDER list, skipping the current one.
        
        NOTE: This button should be hidden/ignored when auto-advance is enabled
        for the current coefficient (either via global or local setting).
        
        Dashboard Location: /Tuning/BayesianTuner/SkipToNextCoefficient
        
        Returns:
            True if the button was pressed (also resets the button state to False)
            False if button not pressed or not connected
        """
        if not self.is_connected():
            return False
        
        try:
            tuner_table = NetworkTables.getTable("/Tuning/BayesianTuner")
            button_pressed = tuner_table.getBoolean("SkipToNextCoefficient", False)
            
            if button_pressed:
                # Reset the button state so it doesn't trigger again
                tuner_table.putBoolean("SkipToNextCoefficient", False)
                logger.info("Skip to Next Coefficient button pressed")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error reading skip button: {e}")
            return False
    
    def read_global_threshold_update(self) -> int:
        """
        Read if the user wants to update the GLOBAL shot threshold at runtime.
        
        This changes the default threshold used by all coefficients that don't
        have their own override.
        
        Dashboard provides:
        - NewGlobalThreshold: Input field for new global value
        - UpdateGlobalThreshold: Button to apply the new global value
        
        Dashboard Location: /Tuning/BayesianTuner/
        
        Returns:
            The new global threshold value if update requested, -1 otherwise
        """
        if not self.is_connected():
            return -1
        
        try:
            tuner_table = NetworkTables.getTable("/Tuning/BayesianTuner")
            update_pressed = tuner_table.getBoolean("UpdateGlobalThreshold", False)
            
            if update_pressed:
                # Reset the button
                tuner_table.putBoolean("UpdateGlobalThreshold", False)
                # Get the new threshold value
                new_threshold = int(tuner_table.getNumber("NewGlobalThreshold", 10))
                logger.info(f"Global shot threshold update requested: {new_threshold}")
                return new_threshold
            
            return -1
        except Exception as e:
            logger.error(f"Error reading global threshold update: {e}")
            return -1
    
    def read_local_threshold_update(self) -> int:
        """
        Read if the user wants to update the LOCAL shot threshold at runtime.
        
        This changes the threshold for the CURRENT coefficient only,
        enabling its autotune_override if not already enabled.
        
        Dashboard provides:
        - NewLocalThreshold: Input field for new local value (current coeff only)
        - UpdateLocalThreshold: Button to apply the new local value
        
        Dashboard Location: /Tuning/BayesianTuner/
        
        Returns:
            The new local threshold value if update requested, -1 otherwise
        """
        if not self.is_connected():
            return -1
        
        try:
            tuner_table = NetworkTables.getTable("/Tuning/BayesianTuner")
            update_pressed = tuner_table.getBoolean("UpdateLocalThreshold", False)
            
            if update_pressed:
                # Reset the button
                tuner_table.putBoolean("UpdateLocalThreshold", False)
                # Get the new threshold value
                new_threshold = int(tuner_table.getNumber("NewLocalThreshold", 10))
                logger.info(f"Local shot threshold update requested: {new_threshold}")
                return new_threshold
            
            return -1
        except Exception as e:
            logger.error(f"Error reading local threshold update: {e}")
            return -1
    
    def write_current_coefficient_info(self, coeff_name: str, is_autotune: bool, shot_threshold: int, auto_advance: bool):
        """
        Write current coefficient tuning info to dashboard.
        
        This lets the dashboard display which coefficient is being tuned
        and its specific settings. Also controls button visibility:
        
        - RunOptimization button: Only visible when is_autotune = False (manual mode)
        - SkipToNextCoefficient button: Only visible when auto_advance = False
        
        Args:
            coeff_name: Name of current coefficient being tuned
            is_autotune: Whether this coefficient uses autotune mode (effective value)
            shot_threshold: Shot threshold for this coefficient (effective value)
            auto_advance: Whether auto-advance is enabled for this coefficient (effective value)
        """
        if not self.is_connected():
            return
        
        try:
            tuner_table = NetworkTables.getTable("/Tuning/BayesianTuner")
            tuner_table.putString("CurrentCoefficient", coeff_name)
            tuner_table.putBoolean("CurrentCoeffAutotune", is_autotune)
            tuner_table.putNumber("CurrentCoeffThreshold", shot_threshold)
            tuner_table.putBoolean("CurrentCoeffAutoAdvance", auto_advance)
            
            # ── RunOptimization button visibility ──
            # Only show when this coefficient uses MANUAL mode (autotune disabled)
            # Dashboard should check CurrentCoeffAutotune to show/hide this button
            tuner_table.putBoolean("ShowRunOptimizationButton", not is_autotune)
            if not is_autotune:
                # Make sure button exists for manual mode
                if not tuner_table.containsKey("RunOptimization"):
                    tuner_table.putBoolean("RunOptimization", False)
            
            # ── SkipToNextCoefficient button visibility ──
            # Only show when auto-advance is DISABLED for this coefficient
            # When auto-advance is on, the tuner will automatically skip on 100% success
            tuner_table.putBoolean("ShowSkipButton", not auto_advance)
            if not auto_advance:
                # Make sure button exists when manual skip is needed
                if not tuner_table.containsKey("SkipToNextCoefficient"):
                    tuner_table.putBoolean("SkipToNextCoefficient", False)
            
        except Exception as e:
            logger.error(f"Error writing coefficient info: {e}")
    
    def read_tuner_enabled_toggle(self) -> tuple:
        """
        Read the runtime tuner enable/disable toggle from the dashboard.
        
        This allows drivers to enable or disable the entire BayesOpt tuner
        at runtime via the dashboard, without needing to restart the program.
        
        The toggle works like a simple on/off switch - when the driver
        changes the value on the dashboard, it takes effect immediately.
        
        Dashboard Location: /Tuning/BayesianTuner/TunerEnabled
        
        Returns:
            Tuple of (was_changed, new_value):
            - was_changed: True if the toggle value changed from last read
            - new_value: The new value of the toggle (True = enabled, False = disabled)
        """
        if not self.is_connected():
            return (False, True)  # Default to enabled if not connected
        
        try:
            tuner_table = NetworkTables.getTable("/Tuning/BayesianTuner")
            
            # Read the current toggle value from dashboard
            current_value = tuner_table.getBoolean("TunerEnabled", True)
            
            # Track the previous value to detect changes
            if not hasattr(self, '_last_tuner_enabled_value'):
                self._last_tuner_enabled_value = current_value
                return (False, current_value)
            
            # Check if value changed since last read
            if current_value != self._last_tuner_enabled_value:
                self._last_tuner_enabled_value = current_value
                logger.info(f"Tuner enabled toggle changed to: {current_value}")
                return (True, current_value)
            
            return (False, current_value)
        except Exception as e:
            logger.error(f"Error reading tuner enabled toggle: {e}")
            return (False, True)
    
    def write_tuner_enabled_status(self, enabled: bool, paused: bool = False):
        """
        Write the tuner enabled status to the dashboard.
        
        This publishes the current state of the tuner so drivers can see
        whether the tuner is enabled/disabled and toggle it.
        
        The TunerEnabled toggle works as a direct on/off switch - when the
        driver changes it on the dashboard, the tuner will enable/disable
        immediately without needing to press any additional buttons.
        
        Dashboard Location: /Tuning/BayesianTuner/
        Published Values:
            - TunerEnabled (bool): Toggle to enable/disable the tuner at runtime
            - TunerPaused (bool): Whether the tuner is paused (e.g., match mode)
            - TunerStatus (string): Human-readable status message
        
        Args:
            enabled: Whether the tuner is currently enabled
            paused: Whether the tuner is paused (but still enabled)
        """
        if not self.is_connected():
            return
        
        try:
            tuner_table = NetworkTables.getTable("/Tuning/BayesianTuner")
            
            # Initialize TunerEnabled toggle on first write (only if it doesn't exist)
            # This preserves user changes made on the dashboard
            if not tuner_table.containsKey("TunerEnabled"):
                tuner_table.putBoolean("TunerEnabled", enabled)
            
            tuner_table.putBoolean("TunerPaused", paused)
            
            # Write human-readable status for dashboard display
            if not enabled:
                status = "DISABLED (toggle TunerEnabled to enable)"
            elif paused:
                status = "PAUSED (match mode detected)"
            else:
                status = "ACTIVE"
            tuner_table.putString("TunerRuntimeStatus", status)
            
            logger.debug(f"Tuner status: enabled={enabled}, paused={paused}")
        except Exception as e:
            logger.error(f"Error writing tuner enabled status: {e}")
    
    def initialize_manual_controls(self, coefficients: dict):
        """
        Initialize manual coefficient adjustment controls on the dashboard.
        
        This allows drivers to manually adjust any coefficient value in real-time
        from the dashboard without waiting for optimization.
        
        Dashboard Location: /Tuning/BayesianTuner/ManualControl/
        
        Controls:
            - ManualAdjustEnabled (bool): Enable manual adjustment mode
            - CoefficientSelector (string): Which coefficient to adjust
            - NewValue (number): Value to set
            - ApplyManualValue (bool): Button to apply the change
            - CurrentValue (number): Shows current value of selected coefficient
            - AvailableCoefficients (string): Comma-separated list of coefficient names
        
        Args:
            coefficients: Dict of coefficient names to CoefficientConfig objects
        """
        if not self.is_connected():
            return
        
        try:
            manual_table = NetworkTables.getTable("/Tuning/BayesianTuner/ManualControl")
            
            # Initialize controls if they don't exist
            if not manual_table.containsKey("ManualAdjustEnabled"):
                manual_table.putBoolean("ManualAdjustEnabled", False)
            
            # List of available coefficients for selection
            coeff_names = ",".join(coefficients.keys())
            manual_table.putString("AvailableCoefficients", coeff_names)
            
            # Initialize selector with first coefficient
            if not manual_table.containsKey("CoefficientSelector"):
                first_coeff = list(coefficients.keys())[0] if coefficients else ""
                manual_table.putString("CoefficientSelector", first_coeff)
            
            if not manual_table.containsKey("NewValue"):
                manual_table.putNumber("NewValue", 0.0)
            
            if not manual_table.containsKey("ApplyManualValue"):
                manual_table.putBoolean("ApplyManualValue", False)
            
            if not manual_table.containsKey("CurrentValue"):
                manual_table.putNumber("CurrentValue", 0.0)
            
            logger.info("Manual coefficient controls initialized on dashboard")
        except Exception as e:
            logger.error(f"Error initializing manual controls: {e}")
    
    def read_manual_coefficient_adjustment(self) -> tuple:
        """
        Read manual coefficient adjustment request from dashboard.
        
        Allows drivers to manually set any coefficient value in real-time.
        
        Dashboard Location: /Tuning/BayesianTuner/ManualControl/
        
        Returns:
            Tuple of (triggered, coefficient_name, new_value):
            - triggered: True if the apply button was pressed
            - coefficient_name: Name of coefficient to adjust
            - new_value: New value to set
        """
        if not self.is_connected():
            return (False, "", 0.0)
        
        try:
            manual_table = NetworkTables.getTable("/Tuning/BayesianTuner/ManualControl")
            
            # Check if adjustment is enabled
            if not manual_table.getBoolean("ManualAdjustEnabled", False):
                return (False, "", 0.0)
            
            # Check if apply button was pressed
            apply_pressed = manual_table.getBoolean("ApplyManualValue", False)
            
            if apply_pressed:
                # Reset button
                manual_table.putBoolean("ApplyManualValue", False)
                
                # Get the coefficient name and new value
                coeff_name = manual_table.getString("CoefficientSelector", "")
                new_value = manual_table.getNumber("NewValue", 0.0)
                
                logger.info(f"Manual coefficient adjustment: {coeff_name} = {new_value}")
                return (True, coeff_name, new_value)
            
            return (False, "", 0.0)
        except Exception as e:
            logger.error(f"Error reading manual adjustment: {e}")
            return (False, "", 0.0)
    
    def write_manual_control_status(self, coeff_name: str, current_value: float, min_val: float, max_val: float):
        """
        Write current coefficient info to manual control section.
        
        Updates the dashboard with the current value and valid range
        for the selected coefficient.
        
        Args:
            coeff_name: Name of currently selected coefficient
            current_value: Current value of the coefficient
            min_val: Minimum allowed value
            max_val: Maximum allowed value
        """
        if not self.is_connected():
            return
        
        try:
            manual_table = NetworkTables.getTable("/Tuning/BayesianTuner/ManualControl")
            manual_table.putNumber("CurrentValue", current_value)
            manual_table.putNumber("MinValue", min_val)
            manual_table.putNumber("MaxValue", max_val)
            manual_table.putString("SelectedCoefficient", coeff_name)
        except Exception as e:
            logger.error(f"Error writing manual control status: {e}")
    
    def initialize_fine_tuning_controls(self):
        """
        Initialize fine-tuning mode controls on the dashboard.
        
        Fine-tuning mode is used after the robot is consistently hitting the target.
        It allows adjusting where within the target you want to hit (center, edges, etc.)
        
        Dashboard Location: /Tuning/BayesianTuner/FineTuning/
        
        Controls:
            - FineTuningEnabled (bool): Enable fine-tuning mode
            - TargetBias (string): "CENTER", "LEFT", "RIGHT", "UP", "DOWN"
            - BiasAmount (number): How much to bias (0.0 = center, 1.0 = edge)
        """
        if not self.is_connected():
            return
        
        try:
            fine_table = NetworkTables.getTable("/Tuning/BayesianTuner/FineTuning")
            
            if not fine_table.containsKey("FineTuningEnabled"):
                fine_table.putBoolean("FineTuningEnabled", False)
            
            if not fine_table.containsKey("TargetBias"):
                fine_table.putString("TargetBias", "CENTER")
            
            if not fine_table.containsKey("BiasAmount"):
                fine_table.putNumber("BiasAmount", 0.0)
            
            # Provide valid options for dashboard dropdown
            fine_table.putString("ValidBiasOptions", "CENTER,LEFT,RIGHT,UP,DOWN")
            
            logger.info("Fine-tuning controls initialized on dashboard")
        except Exception as e:
            logger.error(f"Error initializing fine-tuning controls: {e}")
    
    def read_fine_tuning_settings(self) -> tuple:
        """
        Read fine-tuning settings from dashboard.
        
        Returns:
            Tuple of (enabled, target_bias, bias_amount):
            - enabled: Whether fine-tuning mode is active
            - target_bias: "CENTER", "LEFT", "RIGHT", "UP", "DOWN"
            - bias_amount: 0.0-1.0 (how much to bias)
        """
        if not self.is_connected():
            return (False, "CENTER", 0.0)
        
        try:
            fine_table = NetworkTables.getTable("/Tuning/BayesianTuner/FineTuning")
            enabled = fine_table.getBoolean("FineTuningEnabled", False)
            target_bias = fine_table.getString("TargetBias", "CENTER")
            bias_amount = fine_table.getNumber("BiasAmount", 0.0)
            
            return (enabled, target_bias, bias_amount)
        except Exception as e:
            logger.error(f"Error reading fine-tuning settings: {e}")
            return (False, "CENTER", 0.0)
    
    def initialize_backtrack_controls(self, tuning_order: list):
        """
        Initialize backtrack tuning controls on the dashboard.
        
        Backtracking allows the tuner to go back to a previously tuned
        coefficient if inaccuracy is caused by improper earlier tuning.
        
        Dashboard Location: /Tuning/BayesianTuner/Backtrack/
        
        Controls:
            - BacktrackEnabled (bool): Allow backtracking
            - BacktrackToCoefficient (string): Name of coefficient to backtrack to
            - TriggerBacktrack (bool): Button to trigger backtrack
            - TunedCoefficients (string): Comma-separated list of already tuned coefficients
        
        Args:
            tuning_order: List of coefficient names in tuning order
        """
        if not self.is_connected():
            return
        
        try:
            backtrack_table = NetworkTables.getTable("/Tuning/BayesianTuner/Backtrack")
            
            if not backtrack_table.containsKey("BacktrackEnabled"):
                backtrack_table.putBoolean("BacktrackEnabled", False)
            
            if not backtrack_table.containsKey("TriggerBacktrack"):
                backtrack_table.putBoolean("TriggerBacktrack", False)
            
            # Provide tuning order for reference
            backtrack_table.putString("TuningOrder", ",".join(tuning_order))
            
            if not backtrack_table.containsKey("BacktrackToCoefficient"):
                backtrack_table.putString("BacktrackToCoefficient", "")
            
            logger.info("Backtrack controls initialized on dashboard")
        except Exception as e:
            logger.error(f"Error initializing backtrack controls: {e}")
    
    def read_backtrack_request(self) -> tuple:
        """
        Read backtrack request from dashboard.
        
        Returns:
            Tuple of (triggered, coefficient_name):
            - triggered: True if backtrack button was pressed
            - coefficient_name: Name of coefficient to backtrack to
        """
        if not self.is_connected():
            return (False, "")
        
        try:
            backtrack_table = NetworkTables.getTable("/Tuning/BayesianTuner/Backtrack")
            
            # Check if backtracking is enabled
            if not backtrack_table.getBoolean("BacktrackEnabled", False):
                return (False, "")
            
            # Check if trigger button was pressed
            triggered = backtrack_table.getBoolean("TriggerBacktrack", False)
            
            if triggered:
                # Reset button
                backtrack_table.putBoolean("TriggerBacktrack", False)
                
                coeff_name = backtrack_table.getString("BacktrackToCoefficient", "")
                logger.info(f"Backtrack requested to: {coeff_name}")
                return (True, coeff_name)
            
            return (False, "")
        except Exception as e:
            logger.error(f"Error reading backtrack request: {e}")
            return (False, "")
    
    def write_backtrack_status(self, tuned_coefficients: list, current_coefficient: str):
        """
        Write backtrack status to dashboard.
        
        Updates the dashboard with which coefficients have been tuned
        and can be backtracked to.
        
        Args:
            tuned_coefficients: List of coefficient names already tuned
            current_coefficient: Name of currently tuning coefficient
        """
        if not self.is_connected():
            return
        
        try:
            backtrack_table = NetworkTables.getTable("/Tuning/BayesianTuner/Backtrack")
            backtrack_table.putString("TunedCoefficients", ",".join(tuned_coefficients))
            backtrack_table.putString("CurrentCoefficient", current_coefficient)
        except Exception as e:
            logger.error(f"Error writing backtrack status: {e}")
    
    def write_all_coefficient_values_to_dashboard(self, coefficient_values: dict, coefficients: dict):
        """
        Write ALL current coefficient values to dashboard for monitoring.
        
        This allows drivers to see the current operating values of all
        coefficients at any time, comparing them to code defaults.
        
        Dashboard Location: /Tuning/BayesianTuner/CoefficientsLive/
        
        For each coefficient, publishes:
            - {CoeffName}/CurrentValue: The current operating value
            - {CoeffName}/CodeDefault: The default from COEFFICIENT_TUNING.py
            - {CoeffName}/Difference: Difference between current and default
        
        Args:
            coefficient_values: Dict of current coefficient values
            coefficients: Dict of CoefficientConfig objects (for defaults)
        """
        if not self.is_connected():
            return
        
        try:
            live_table = NetworkTables.getTable("/Tuning/BayesianTuner/CoefficientsLive")
            
            for name, current_val in coefficient_values.items():
                if name in coefficients:
                    coeff = coefficients[name]
                    default_val = coeff.default_value
                    difference = current_val - default_val
                    
                    coeff_table = live_table.getSubTable(name)
                    coeff_table.putNumber("CurrentValue", current_val)
                    coeff_table.putNumber("CodeDefault", default_val)
                    coeff_table.putNumber("Difference", difference)
                    coeff_table.putNumber("MinValue", coeff.min_value)
                    coeff_table.putNumber("MaxValue", coeff.max_value)
                    coeff_table.putBoolean("Enabled", coeff.enabled)
        except Exception as e:
            logger.error(f"Error writing coefficient values to dashboard: {e}")
            
