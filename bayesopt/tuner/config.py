"""
Configuration module for the FRC Shooter Bayesian Tuner.

This module loads configuration from two simple files:
1. TUNER_TOGGLES.ini - Three main on/off switches
2. COEFFICIENT_TUNING.py - What to tune, how much, in what order

NO NEED TO EDIT THIS FILE - edit the files above instead!
"""

from dataclasses import dataclass
from typing import Dict, List
import os
import configparser
import importlib.util


@dataclass
class CoefficientConfig:
    """Configuration for a single tunable coefficient."""
    
    name: str
    default_value: float
    min_value: float
    max_value: float
    initial_step_size: float
    step_decay_rate: float
    is_integer: bool
    enabled: bool
    nt_key: str  # NetworkTables key path
    
    def clamp(self, value: float) -> float:
        """Clamp value to valid range."""
        clamped = max(self.min_value, min(self.max_value, value))
        if self.is_integer:
            clamped = round(clamped)
        return clamped


class TunerConfig:
    """
    Global configuration for the Bayesian tuner system.
    
    Loads settings from:
    - TUNER_TOGGLES.ini (main on/off switches)
    - COEFFICIENT_TUNING.py (coefficient definitions and tuning order)
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
        """Load the three main toggles from TUNER_TOGGLES.ini"""
        # Find the toggles file (in ../config/ relative to tuner module)
        module_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(module_dir)
        toggles_file = os.path.join(parent_dir, "config", "TUNER_TOGGLES.ini")
        
        config = configparser.ConfigParser()
        config.read(toggles_file)
        
        # Load main controls
        self.TUNER_ENABLED = config.getboolean('main_controls', 'tuner_enabled', fallback=True)
        self.REQUIRE_SHOT_LOGGED = config.getboolean('main_controls', 'require_shot_logged', fallback=False)
        self.REQUIRE_COEFFICIENTS_UPDATED = config.getboolean('main_controls', 'require_coefficients_updated', fallback=False)
        
        # Load team number and calculate robot IP
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
        
        return warnings
    