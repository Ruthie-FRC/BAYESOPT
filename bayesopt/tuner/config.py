"""
Configuration module for the FRC Shooter Bayesian Tuner.

This module loads configuration from two simple files:
1. TUNER_TOGGLES.ini - Main on/off switches and autotune settings
2. COEFFICIENT_TUNING.py - What to tune, how much, in what order

NO NEED TO EDIT THIS FILE - edit the files above instead!

Configuration Options Loaded:
-----------------------------
From TUNER_TOGGLES.ini:
    - TUNER_ENABLED: Master switch to enable/disable the tuner
    - AUTOTUNE_ENABLED: Toggle between automatic and manual optimization
    - AUTOTUNE_SHOT_THRESHOLD: Number of shots before auto-optimization runs
    - REQUIRE_SHOT_LOGGED: Shooting interlock setting
    - REQUIRE_COEFFICIENTS_UPDATED: Coefficient interlock setting
    - Team number (for robot IP calculation)

From COEFFICIENT_TUNING.py:
    - COEFFICIENTS: Dictionary of tunable coefficients with their bounds
    - TUNING_ORDER: Order in which coefficients are optimized
    - Optimization parameters (N_INITIAL_POINTS, N_CALLS_PER_COEFFICIENT, etc.)
"""

from dataclasses import dataclass
from typing import Dict, List
import os
import configparser
import importlib.util


@dataclass
class CoefficientConfig:
    """
    Configuration for a single tunable coefficient.
    
    Attributes:
        name: Human-readable name of the coefficient (e.g., "kDragCoefficient")
        default_value: Starting value for optimization
        min_value: Minimum allowed value (safety limit)
        max_value: Maximum allowed value (safety limit)
        initial_step_size: How much to change the value in early iterations
        step_decay_rate: How quickly to reduce step size (0.9 = shrink 10% per iteration)
        is_integer: If True, round values to whole numbers
        enabled: If True, this coefficient will be tuned
        nt_key: NetworkTables key path for reading/writing this coefficient
        autotune_override: If True, use per-coefficient autotune settings instead of global
        autotune_enabled: Per-coefficient autotune toggle (only used if override=True)
        autotune_shot_threshold: Per-coefficient sample size (only used if override=True)
        auto_advance_override: If True, use per-coefficient auto-advance setting instead of global
        auto_advance_on_success: Per-coefficient auto-advance on 100% success (only used if override=True)
    """
    
    name: str
    default_value: float
    min_value: float
    max_value: float
    initial_step_size: float
    step_decay_rate: float
    is_integer: bool
    enabled: bool
    nt_key: str  # NetworkTables key path
    # Per-coefficient autotune settings
    autotune_override: bool = False  # If True, use custom settings below instead of global
    autotune_enabled: bool = False   # Custom autotune toggle (only used if override=True)
    autotune_shot_threshold: int = 10  # Custom sample size (only used if override=True)
    # Per-coefficient auto-advance settings
    auto_advance_override: bool = False  # If True, use custom settings below instead of global
    auto_advance_on_success: bool = False  # Auto-advance on 100% success (only used if override=True)
    auto_advance_shot_threshold: int = 10  # Custom threshold for auto-advance (only used if override=True)
    
    def clamp(self, value: float) -> float:
        """
        Clamp value to valid range and optionally round to integer.
        
        Args:
            value: The value to clamp
            
        Returns:
            Value clamped to [min_value, max_value], rounded if is_integer=True
        """
        clamped = max(self.min_value, min(self.max_value, value))
        if self.is_integer:
            clamped = round(clamped)
        return clamped
    
    def get_effective_autotune_settings(self, global_enabled: bool, global_threshold: int, force_global: bool = False) -> tuple:
        """
        Get the effective autotune settings for this coefficient.
        
        Priority: force_global > local override > global default
        
        Args:
            global_enabled: Global autotune_enabled from TUNER_TOGGLES.ini
            global_threshold: Global autotune_shot_threshold from TUNER_TOGGLES.ini
            force_global: If True, ignores local override and uses global settings
            
        Returns:
            Tuple of (autotune_enabled, autotune_shot_threshold) to use for this coefficient
        """
        if force_global:
            # Force global: ignore all local overrides
            return (global_enabled, global_threshold)
        elif self.autotune_override:
            # Local override takes precedence over global default
            return (self.autotune_enabled, self.autotune_shot_threshold)
        else:
            # Use global default
            return (global_enabled, global_threshold)
    
    def get_effective_auto_advance_settings(self, global_auto_advance: bool, global_threshold: int, force_global: bool = False) -> tuple:
        """
        Get the effective auto-advance settings for this coefficient.
        
        Priority: force_global > local override > global default
        
        Args:
            global_auto_advance: Global auto_advance_on_success from TUNER_TOGGLES.ini
            global_threshold: Global auto_advance_shot_threshold from TUNER_TOGGLES.ini
            force_global: If True, ignores local override and uses global settings
            
        Returns:
            Tuple of (auto_advance_enabled, auto_advance_shot_threshold) to use for this coefficient
        """
        if force_global:
            # Force global: ignore all local overrides
            return (global_auto_advance, global_threshold)
        elif self.auto_advance_override:
            # Local override takes precedence over global default
            return (self.auto_advance_on_success, self.auto_advance_shot_threshold)
        else:
            # Use global default
            return (global_auto_advance, global_threshold)
    
    def get_effective_auto_advance(self, global_auto_advance: bool, force_global: bool = False) -> bool:
        """
        Get the effective auto-advance enabled setting for this coefficient.
        
        Priority: force_global > local override > global default
        
        Args:
            global_auto_advance: Global auto_advance_on_success from TUNER_TOGGLES.ini
            force_global: If True, ignores local override and uses global settings
            
        Returns:
            Whether to auto-advance on 100% success for this coefficient
        """
        if force_global:
            return global_auto_advance
        elif self.auto_advance_override:
            return self.auto_advance_on_success
        else:
            return global_auto_advance


class TunerConfig:
    """
    Global configuration for the Bayesian tuner system.
    
    This class loads and manages all tuner settings. It reads from two files:
    - TUNER_TOGGLES.ini: Main toggles including autotune mode
    - COEFFICIENT_TUNING.py: Coefficient definitions and optimization settings
    
    Key Attributes:
        TUNER_ENABLED (bool): Master switch - if False, tuner does nothing
        AUTOTUNE_ENABLED (bool): If True, auto-optimize after threshold shots;
                                  if False, wait for dashboard button press
        AUTOTUNE_SHOT_THRESHOLD (int): Number of shots to collect before 
                                        automatic optimization (sample size)
        COEFFICIENTS (dict): Map of coefficient names to CoefficientConfig objects
        TUNING_ORDER (list): Order in which to optimize coefficients
    """
    
    def __init__(self):
        """Initialize configuration by loading from files."""
        # Load toggle settings from TUNER_TOGGLES.ini
        self._load_toggles()
        
        # Load coefficient configuration from COEFFICIENT_TUNING.py
        self._load_coefficient_config()
        
        # Initialize other settings
        self._initialize_constants()
    
    def _load_toggles(self):
        """
        Load the main toggles from TUNER_TOGGLES.ini.
        
        This loads:
        - TUNER_ENABLED: Master on/off switch
        - AUTOTUNE_ENABLED: Automatic vs manual optimization mode
        - AUTOTUNE_SHOT_THRESHOLD: Sample size for automatic mode
        - AUTOTUNE_FORCE_GLOBAL: When True, ignores local overrides
        - AUTO_ADVANCE_ON_SUCCESS: Auto-advance on 100% success
        - AUTO_ADVANCE_SHOT_THRESHOLD: Sample size for auto-advance
        - AUTO_ADVANCE_FORCE_GLOBAL: When True, ignores local overrides
        - REQUIRE_SHOT_LOGGED: Shooting interlock
        - REQUIRE_COEFFICIENTS_UPDATED: Coefficient interlock
        - NT_SERVER_IP: Calculated from team number
        """
        # Find the toggles file (in ../config/ relative to tuner module)
        module_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(module_dir)
        toggles_file = os.path.join(parent_dir, "config", "TUNER_TOGGLES.ini")
        
        config = configparser.ConfigParser()
        config.read(toggles_file)
        
        # ── Master Switch ──
        self.TUNER_ENABLED = config.getboolean('main_controls', 'tuner_enabled', fallback=True)
        
        # ── Autotune Settings ──
        self.AUTOTUNE_ENABLED = config.getboolean('main_controls', 'autotune_enabled', fallback=False)
        self.AUTOTUNE_SHOT_THRESHOLD = config.getint('main_controls', 'autotune_shot_threshold', fallback=10)
        # FORCE_GLOBAL: When True, ignores ALL local coefficient overrides for autotune
        self.AUTOTUNE_FORCE_GLOBAL = config.getboolean('main_controls', 'autotune_force_global', fallback=False)
        
        # ── Auto-Advance Settings ──
        self.AUTO_ADVANCE_ON_SUCCESS = config.getboolean('main_controls', 'auto_advance_on_success', fallback=False)
        self.AUTO_ADVANCE_SHOT_THRESHOLD = config.getint('main_controls', 'auto_advance_shot_threshold', fallback=10)
        # FORCE_GLOBAL: When True, ignores ALL local coefficient overrides for auto-advance
        self.AUTO_ADVANCE_FORCE_GLOBAL = config.getboolean('main_controls', 'auto_advance_force_global', fallback=False)
        
        # ── Shooting Interlocks ──
        self.REQUIRE_SHOT_LOGGED = config.getboolean('main_controls', 'require_shot_logged', fallback=False)
        self.REQUIRE_COEFFICIENTS_UPDATED = config.getboolean('main_controls', 'require_coefficients_updated', fallback=False)
        
        # ── Team/Network Configuration ──
        team_number = config.getint('team', 'team_number', fallback=5892)
        self.NT_SERVER_IP = f"10.{team_number // 100}.{team_number % 100}.2"
    
    def _load_coefficient_config(self):
        """Load coefficient definitions from COEFFICIENT_TUNING.py"""
        # Find the coefficient config file (in ../config/ relative to tuner module)
        module_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(module_dir)
        coeff_file = os.path.join(parent_dir, "config", "COEFFICIENT_TUNING.py")
        
        # Load as module
        spec = importlib.util.spec_from_file_location("coeff_config", coeff_file)
        coeff_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(coeff_module)
        
        # Load tuning order
        self.TUNING_ORDER = coeff_module.TUNING_ORDER
        
        # Convert coefficient dicts to CoefficientConfig objects
        self.COEFFICIENTS = {}
        for name, cfg in coeff_module.COEFFICIENTS.items():
            self.COEFFICIENTS[name] = CoefficientConfig(
                name=name,
                default_value=cfg['default_value'],
                min_value=cfg['min_value'],
                max_value=cfg['max_value'],
                initial_step_size=cfg['initial_step_size'],
                step_decay_rate=cfg['step_decay_rate'],
                is_integer=cfg['is_integer'],
                enabled=cfg['enabled'],
                nt_key=cfg['nt_key'],
                # Per-coefficient autotune settings (default to global if not specified)
                autotune_override=cfg.get('autotune_override', False),
                autotune_enabled=cfg.get('autotune_enabled', False),
                autotune_shot_threshold=cfg.get('autotune_shot_threshold', 10),
                # Per-coefficient auto-advance settings
                auto_advance_override=cfg.get('auto_advance_override', False),
                auto_advance_on_success=cfg.get('auto_advance_on_success', False),
                auto_advance_shot_threshold=cfg.get('auto_advance_shot_threshold', 10),
            )
        
        # Load optimization settings
        self.N_INITIAL_POINTS = coeff_module.N_INITIAL_POINTS
        self.N_CALLS_PER_COEFFICIENT = coeff_module.N_CALLS_PER_COEFFICIENT
        
        # Load RoboRIO protection settings
        self.MAX_NT_WRITE_RATE_HZ = coeff_module.MAX_WRITE_RATE_HZ
        self.MAX_NT_READ_RATE_HZ = coeff_module.MAX_READ_RATE_HZ
        self.NT_BATCH_WRITES = coeff_module.BATCH_WRITES
        
        # Load physical limits
        self.PHYSICAL_MAX_VELOCITY_MPS = coeff_module.PHYSICAL_MAX_VELOCITY_MPS
        self.PHYSICAL_MIN_VELOCITY_MPS = coeff_module.PHYSICAL_MIN_VELOCITY_MPS
        self.PHYSICAL_MAX_ANGLE_RAD = coeff_module.PHYSICAL_MAX_ANGLE_RAD
        self.PHYSICAL_MIN_ANGLE_RAD = coeff_module.PHYSICAL_MIN_ANGLE_RAD
        self.PHYSICAL_MAX_DISTANCE_M = coeff_module.PHYSICAL_MAX_DISTANCE_M
        self.PHYSICAL_MIN_DISTANCE_M = coeff_module.PHYSICAL_MIN_DISTANCE_M
    
    def _initialize_constants(self):
        """Initialize constants that don't come from config files."""
        # NetworkTables configuration
        self.NT_TIMEOUT_SECONDS = 5.0
        self.NT_RECONNECT_DELAY_SECONDS = 2.0
        
        # NetworkTables keys for shot data
        self.NT_SHOT_DATA_TABLE = "/FiringSolver"
        self.NT_SHOT_HIT_KEY = "/FiringSolver/Hit"
        self.NT_SHOT_DISTANCE_KEY = "/FiringSolver/Distance"
        self.NT_SHOT_ANGLE_KEY = "/FiringSolver/Solution/pitchRadians"
        self.NT_SHOT_VELOCITY_KEY = "/FiringSolver/Solution/exitVelocity"
        self.NT_TUNER_STATUS_KEY = "/FiringSolver/TunerStatus"
        
        # Match mode detection key
        self.NT_MATCH_MODE_KEY = "/FMSInfo/FMSControlData"
        
        # Bayesian optimization settings
        self.ACQUISITION_FUNCTION = "EI"  # Expected Improvement
        
        # Safety and validation
        self.MIN_VALID_SHOTS_BEFORE_UPDATE = 3
        self.MAX_CONSECUTIVE_INVALID_SHOTS = 5
        self.ABNORMAL_READING_THRESHOLD = 3.0  # Standard deviations
        
        # Logging configuration
        self.LOG_DIRECTORY = "./tuner_logs"
        self.LOG_FILENAME_PREFIX = "bayesian_tuner"
        self.LOG_TO_CONSOLE = True
        
        # Threading configuration
        self.TUNER_UPDATE_RATE_HZ = 10.0  # How often to check for new data
        self.GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS = 5.0
        
        # Step size decay configuration
        self.STEP_SIZE_DECAY_ENABLED = True
        self.MIN_STEP_SIZE_RATIO = 0.1  # Minimum step size as ratio of initial
    
    def get_enabled_coefficients_in_order(self) -> List[CoefficientConfig]:
        """Get list of enabled coefficients in tuning order."""
        return [
            self.COEFFICIENTS[name]
            for name in self.TUNING_ORDER
            if name in self.COEFFICIENTS and self.COEFFICIENTS[name].enabled
        ]
    
    def validate_config(self) -> List[str]:
        """
        Validate configuration and return list of warnings.
        
        Returns:
            List of warning messages (empty if no issues)
        """
        warnings = []
        
        # Check that enabled coefficients are in tuning order
        enabled_coeffs = [name for name, cfg in self.COEFFICIENTS.items() if cfg.enabled]
        for name in enabled_coeffs:
            if name not in self.TUNING_ORDER:
                warnings.append(f"Enabled coefficient '{name}' not in TUNING_ORDER")
        
        # Check for coefficients in tuning order that don't exist
        for name in self.TUNING_ORDER:
            if name not in self.COEFFICIENTS:
                warnings.append(f"Coefficient '{name}' in TUNING_ORDER but not defined")
        
        # Validate coefficient configurations
        for name, coeff in self.COEFFICIENTS.items():
            if coeff.min_value >= coeff.max_value:
                warnings.append(f"{name}: min_value must be < max_value")
            
            if coeff.default_value < coeff.min_value or coeff.default_value > coeff.max_value:
                warnings.append(f"{name}: default_value outside valid range")
            
            if coeff.initial_step_size <= 0:
                warnings.append(f"{name}: initial_step_size must be positive")
            
            if not 0 < coeff.step_decay_rate <= 1.0:
                warnings.append(f"{name}: step_decay_rate must be in (0, 1]")
        
        # Validate physical limits make sense
        if self.PHYSICAL_MIN_VELOCITY_MPS >= self.PHYSICAL_MAX_VELOCITY_MPS:
            warnings.append("PHYSICAL_MIN_VELOCITY_MPS >= PHYSICAL_MAX_VELOCITY_MPS")
        
        if self.PHYSICAL_MIN_ANGLE_RAD >= self.PHYSICAL_MAX_ANGLE_RAD:
            warnings.append("PHYSICAL_MIN_ANGLE_RAD >= PHYSICAL_MAX_ANGLE_RAD")
        
        if self.PHYSICAL_MIN_DISTANCE_M >= self.PHYSICAL_MAX_DISTANCE_M:
            warnings.append("PHYSICAL_MIN_DISTANCE_M >= PHYSICAL_MAX_DISTANCE_M")
        
        # Validate system parameters
        if self.N_INITIAL_POINTS < 1:
            warnings.append("N_INITIAL_POINTS must be >= 1")
        
        if self.N_CALLS_PER_COEFFICIENT < self.N_INITIAL_POINTS:
            warnings.append("N_CALLS_PER_COEFFICIENT must be >= N_INITIAL_POINTS")
        
        if self.TUNER_UPDATE_RATE_HZ <= 0:
            warnings.append("TUNER_UPDATE_RATE_HZ must be positive")
        
        # Validate rate limiting parameters to prevent division by zero
        if self.MAX_NT_WRITE_RATE_HZ <= 0:
            warnings.append("MAX_NT_WRITE_RATE_HZ must be positive")
        
        if self.MAX_NT_READ_RATE_HZ <= 0:
            warnings.append("MAX_NT_READ_RATE_HZ must be positive")
        
        return warnings
