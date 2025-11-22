"""
Data logging module for the Bayesian Tuner.

This module handles logging of all tuning data to CSV files for offline analysis.
Logs shot data, coefficient values, step sizes, and NT connection status.
"""

import os
import csv
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class TunerLogger:
    """
    CSV logger for tuner data.
    
    Logs every shot with coefficient values, step sizes, hit/miss results,
    and system status.
    """
    
    def __init__(self, config):
        """
        Initialize tuner logger.
        
        Args:
            config: TunerConfig object
        """
        self.config = config
        self.log_directory = Path(config.LOG_DIRECTORY)
        self.csv_file = None
        self.csv_writer = None
        self.session_start_time = datetime.now()
        
        # Create log directory if it doesn't exist
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize CSV log file
        self._initialize_csv_log()
        
        logger.info(f"Logger initialized, writing to {self.csv_file}")
    
    def _initialize_csv_log(self):
        """Create and initialize CSV log file."""
        # Generate filename with timestamp
        timestamp = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config.LOG_FILENAME_PREFIX}_{timestamp}.csv"
        self.csv_file = self.log_directory / filename
        
        # Create CSV file with headers
        try:
            file_handle = open(self.csv_file, 'w', newline='')
            self.csv_writer = csv.writer(file_handle)
            
            # Write header row - captures ALL robot state at shot time
            headers = [
                'timestamp',
                'session_time_s',
                'coefficient_name',
                'coefficient_value',
                'step_size',
                'iteration',
                'shot_hit',
                'shot_distance',
                'shot_angle_rad',
                'shot_velocity_mps',
                'shot_yaw_rad',
                'target_height_m',
                'launch_height_m',
                'drag_coefficient_used',
                'air_density_used',
                'projectile_mass_kg',
                'projectile_area_m2',
                'nt_connected',
                'match_mode',
                'tuner_status',
                'all_coefficients',
            ]
            self.csv_writer.writerow(headers)
            
            # Store file handle for later closing
            self._file_handle = file_handle
            
            logger.info(f"Created CSV log: {self.csv_file}")
            
        except Exception as e:
            logger.error(f"Failed to create CSV log: {e}")
            self.csv_writer = None
    
    def log_shot(
        self,
        coefficient_name: str,
        coefficient_value: float,
        step_size: float,
        iteration: int,
        shot_data,
        nt_connected: bool,
        match_mode: bool,
        tuner_status: str,
        all_coefficient_values: Dict[str, float]
    ):
        """
        Log a shot to the CSV file.
        
        Args:
            coefficient_name: Name of coefficient being tuned
            coefficient_value: Current value of the coefficient
            step_size: Current step size
            iteration: Current iteration number
            shot_data: ShotData object
            nt_connected: Whether NT is connected
            match_mode: Whether robot is in match mode
            tuner_status: Current tuner status string
            all_coefficient_values: Dict of all coefficient values
        """
        if not self.csv_writer:
            logger.warning("CSV writer not initialized, cannot log")
            return
        
        try:
            current_time = datetime.now()
            session_time = (current_time - self.session_start_time).total_seconds()
            
            # Format all coefficients as JSON-like string
            coeff_str = "; ".join([f"{k}={v:.6f}" for k, v in all_coefficient_values.items()])
            
            # Create row with ALL captured data
            row = [
                current_time.isoformat(),
                f"{session_time:.3f}",
                coefficient_name,
                f"{coefficient_value:.6f}",
                f"{step_size:.6f}",
                iteration,
                shot_data.hit if shot_data else '',
                f"{shot_data.distance:.3f}" if shot_data and shot_data.distance else '',
                f"{shot_data.angle:.6f}" if shot_data and shot_data.angle else '',
                f"{shot_data.velocity:.3f}" if shot_data and shot_data.velocity else '',
                f"{shot_data.yaw:.6f}" if shot_data and hasattr(shot_data, 'yaw') else '',
                f"{shot_data.target_height:.3f}" if shot_data and hasattr(shot_data, 'target_height') else '',
                f"{shot_data.launch_height:.3f}" if shot_data and hasattr(shot_data, 'launch_height') else '',
                f"{shot_data.drag_coefficient:.6f}" if shot_data and hasattr(shot_data, 'drag_coefficient') else '',
                f"{shot_data.air_density:.6f}" if shot_data and hasattr(shot_data, 'air_density') else '',
                f"{shot_data.projectile_mass:.6f}" if shot_data and hasattr(shot_data, 'projectile_mass') else '',
                f"{shot_data.projectile_area:.6f}" if shot_data and hasattr(shot_data, 'projectile_area') else '',
                nt_connected,
                match_mode,
                tuner_status,
                coeff_str,
            ]
            
            self.csv_writer.writerow(row)
            self._file_handle.flush()  # Ensure data is written immediately
            
            logger.debug(f"Logged shot: {coefficient_name}={coefficient_value:.6f}, hit={shot_data.hit if shot_data else 'N/A'}")
            
        except Exception as e:
            logger.error(f"Error logging shot: {e}")
    
    def log_event(self, event_type: str, message: str, data: Optional[Dict] = None):
        """
        Log a system event.
        
        Args:
            event_type: Type of event (e.g., 'START', 'STOP', 'ERROR')
            message: Event message
            data: Optional additional data
        """
        if not self.csv_writer:
            return
        
        try:
            current_time = datetime.now()
            session_time = (current_time - self.session_start_time).total_seconds()
            
            # Log as special row with event info
            row = [
                current_time.isoformat(),
                f"{session_time:.3f}",
                f"EVENT_{event_type}",
                '',  # coefficient_value
                '',  # step_size
                '',  # iteration
                '',  # shot_hit
                '',  # shot_distance
                '',  # shot_angle
                '',  # shot_velocity
                '',  # nt_connected
                '',  # match_mode
                message,
                str(data) if data else '',
            ]
            
            self.csv_writer.writerow(row)
            self._file_handle.flush()
            
            logger.info(f"Logged event: {event_type} - {message}")
            
        except Exception as e:
            logger.error(f"Error logging event: {e}")
    
    def log_statistics(self, statistics: Dict):
        """
        Log optimization statistics.
        
        Args:
            statistics: Dict with optimization statistics
        """
        self.log_event('STATISTICS', 'Optimization statistics', statistics)
    
    def close(self):
        """Close the log file."""
        try:
            if hasattr(self, '_file_handle') and self._file_handle:
                self._file_handle.close()
                logger.info(f"Closed log file: {self.csv_file}")
        except Exception as e:
            logger.error(f"Error closing log file: {e}")
    
    def get_log_file_path(self) -> Optional[Path]:
        """
        Get path to current log file.
        
        Returns:
            Path to log file or None if not initialized
        """
        return self.csv_file
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def setup_logging(config, log_level=logging.INFO):
    """
    Setup logging configuration for the tuner.
    
    Args:
        config: TunerConfig object
        log_level: Logging level (default: INFO)
    """
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler if configured
    if config.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(console_handler)
    
    logger.info("Logging configured")
