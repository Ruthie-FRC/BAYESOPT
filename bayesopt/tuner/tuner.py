"""
Main tuner coordinator module.

This module coordinates all tuner components and runs the tuning loop
in a background thread with safe startup/shutdown.
"""

import time
import threading
import logging
from typing import Optional, Dict

from .config import TunerConfig
from .nt_interface import NetworkTablesInterface, ShotData
from .optimizer import CoefficientTuner
from .logger import TunerLogger, setup_logging


logger = logging.getLogger(__name__)


class BayesianTunerCoordinator:
    """
    Main coordinator for the Bayesian tuner system.
    
    Manages the tuning loop, coordinates between NT interface, optimizer,
    and logger, and handles safe startup/shutdown.
    """
    
    def __init__(self, config: Optional[TunerConfig] = None):
        """
        Initialize tuner coordinator.
        
        Args:
            config: TunerConfig object. If None, uses default config.
        """
        self.config = config or TunerConfig()
        
        # Validate configuration
        warnings = self.config.validate_config()
        if warnings:
            logger.warning(f"Configuration warnings: {warnings}")
        
        # Components
        self.nt_interface = NetworkTablesInterface(self.config)
        self.optimizer = CoefficientTuner(self.config)
        self.data_logger = TunerLogger(self.config)
        
        # State
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_shot_timestamp = 0.0
        
        # Current coefficient values
        self.current_coefficient_values: Dict[str, float] = {}
        
        logger.info("Bayesian Tuner Coordinator initialized")
    
    def start(self, server_ip: Optional[str] = None):
        """
        Start the tuner in a background thread.
        
        Args:
            server_ip: Optional NT server IP. If None, uses config default.
        """
        if self.running:
            logger.warning("Tuner already running")
            return
        
        if not self.config.TUNER_ENABLED:
            logger.info("Tuner is disabled (TUNER_ENABLED = False)")
            return
        
        logger.info("Starting Bayesian Tuner...")
        self.data_logger.log_event('START', 'Tuner starting')
        
        # Connect to NetworkTables
        if not self.nt_interface.connect(server_ip):
            logger.error("Failed to connect to NetworkTables, tuner not started")
            self.data_logger.log_event('ERROR', 'Failed to connect to NT')
            return
        
        # Read initial coefficient values
        self.current_coefficient_values = self.nt_interface.read_all_coefficients(
            self.config.COEFFICIENTS
        )
        logger.info(f"Initial coefficient values: {self.current_coefficient_values}")
        
        # Publish interlock settings to robot
        self.nt_interface.write_interlock_settings(
            self.config.REQUIRE_SHOT_LOGGED,
            self.config.REQUIRE_COEFFICIENTS_UPDATED
        )
        logger.info(f"Interlock settings published: shot_logged={self.config.REQUIRE_SHOT_LOGGED}, "
                   f"coeff_updated={self.config.REQUIRE_COEFFICIENTS_UPDATED}")
        
        # Start tuning thread
        self.running = True
        self.thread = threading.Thread(target=self._tuning_loop, daemon=True)
        self.thread.start()
        
        logger.info("Tuner started successfully")
    
    def stop(self):
        """Stop the tuner gracefully."""
        if not self.running:
            logger.info("Tuner not running")
            return
        
        logger.info("Stopping tuner...")
        self.data_logger.log_event('STOP', 'Tuner stopping')
        
        self.running = False
        
        # Wait for thread to finish
        if self.thread:
            self.thread.join(timeout=self.config.GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS)
            if self.thread.is_alive():
                logger.warning("Tuner thread did not stop gracefully")
        
        # Disconnect from NT
        self.nt_interface.disconnect()
        
        # Close logger
        self.data_logger.close()
        
        logger.info("Tuner stopped")
    
    def _tuning_loop(self):
        """Main tuning loop that runs in background thread."""
        logger.info("Tuning loop started")
        
        update_period = 1.0 / self.config.TUNER_UPDATE_RATE_HZ
        
        while self.running:
            try:
                # Check for safety conditions
                if not self._check_safety_conditions():
                    logger.warning("Safety check failed, pausing tuning")
                    time.sleep(1.0)
                    continue
                
                # Check for new shot data
                shot_data = self.nt_interface.read_shot_data()
                
                if shot_data:
                    self._process_shot(shot_data)
                
                # Suggest next coefficient value if needed
                self._update_coefficients()
                
                # Update status
                self._update_status()
                
                # Sleep until next update
                time.sleep(update_period)
                
            except Exception as e:
                logger.error(f"Error in tuning loop: {e}", exc_info=True)
                time.sleep(1.0)
        
        logger.info("Tuning loop ended")
    
    def _check_safety_conditions(self) -> bool:
        """
        Check safety conditions before continuing tuning.
        
        Returns:
            True if safe to continue, False otherwise
        """
        # Check if tuner is enabled
        if not self.config.TUNER_ENABLED:
            return False
        
        # Check NT connection
        if not self.nt_interface.is_connected():
            logger.warning("NetworkTables disconnected")
            return False
        
        # Check if in match mode
        if self.nt_interface.is_match_mode():
            logger.warning("Match mode detected, pausing tuning")
            return False
        
        return True
    
    def _process_shot(self, shot_data: ShotData):
        """
        Process a new shot result.
        
        Args:
            shot_data: ShotData object
        """
        logger.info(f"Processing shot: hit={shot_data.hit}, distance={shot_data.distance:.2f}m")
        
        # Record shot with optimizer
        self.optimizer.record_shot(shot_data, self.current_coefficient_values)
        
        # Log to CSV
        coeff_name = self.optimizer.get_current_coefficient_name() or "None"
        current_optimizer = self.optimizer.current_optimizer
        
        coefficient_value = 0.0
        step_size = 0.0
        iteration = 0
        
        if current_optimizer:
            coeff_name = current_optimizer.coeff_config.name
            coefficient_value = self.current_coefficient_values.get(
                coeff_name,
                current_optimizer.coeff_config.default_value
            )
            step_size = current_optimizer.current_step_size
            iteration = current_optimizer.iteration
        
        self.data_logger.log_shot(
            coefficient_name=coeff_name,
            coefficient_value=coefficient_value,
            step_size=step_size,
            iteration=iteration,
            shot_data=shot_data,
            nt_connected=self.nt_interface.is_connected(),
            match_mode=self.nt_interface.is_match_mode(),
            tuner_status=self.optimizer.get_tuning_status(),
            all_coefficient_values=self.current_coefficient_values,
        )
    
    def _update_coefficients(self):
        """Update coefficients based on optimizer suggestions."""
        suggestion = self.optimizer.suggest_coefficient_update()
        
        if suggestion:
            coeff_name, new_value = suggestion
            
            # Update in NT
            coeff_config = self.config.COEFFICIENTS[coeff_name]
            success = self.nt_interface.write_coefficient(coeff_config.nt_key, new_value)
            
            if success:
                # Update local tracking
                self.current_coefficient_values[coeff_name] = new_value
                logger.info(f"Updated {coeff_name} = {new_value:.6f}")
                
                # Signal interlock system that coefficients are updated
                self.nt_interface.signal_coefficients_updated()
            else:
                logger.error(f"Failed to write {coeff_name} to NT")
    
    def _update_status(self):
        """Update tuner status in NetworkTables for driver feedback."""
        status = self.optimizer.get_tuning_status()
        
        # Add step size info if tuning
        if self.optimizer.current_optimizer:
            step_size = self.optimizer.current_optimizer.current_step_size
            status += f" | step: {step_size:.6f}"
        
        self.nt_interface.write_status(status)
    
    def get_status(self) -> Dict:
        """
        Get current tuner status.
        
        Returns:
            Dict with status information
        """
        status = {
            'running': self.running,
            'enabled': self.config.TUNER_ENABLED,
            'nt_connected': self.nt_interface.is_connected(),
            'match_mode': self.nt_interface.is_match_mode(),
            'tuning_status': self.optimizer.get_tuning_status(),
            'is_complete': self.optimizer.is_complete(),
            'current_coefficient': self.optimizer.get_current_coefficient_name(),
            'log_file': str(self.data_logger.get_log_file_path()),
        }
        
        if self.optimizer.current_optimizer:
            status['optimizer_stats'] = self.optimizer.current_optimizer.get_statistics()
        
        return status
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def run_tuner(server_ip: Optional[str] = None, config: Optional[TunerConfig] = None):
    """
    Convenience function to run the tuner.
    
    Args:
        server_ip: Optional NT server IP
        config: Optional TunerConfig object
    """
    # Setup logging
    if config:
        setup_logging(config)
    else:
        setup_logging(TunerConfig())
    
    logger.info("="*60)
    logger.info("FRC Shooter Bayesian Tuner")
    logger.info("="*60)
    
    # Create and run tuner
    with BayesianTunerCoordinator(config) as tuner:
        try:
            logger.info("Tuner running. Press Ctrl+C to stop.")
            
            # Keep running until interrupted
            while not tuner.optimizer.is_complete():
                time.sleep(1.0)
                
                # Print periodic status
                status = tuner.get_status()
                if status['running']:
                    logger.info(f"Status: {status['tuning_status']}")
            
            logger.info("Tuning complete!")
            
            # Log final statistics
            for optimizer in tuner.optimizer.completed_coefficients:
                stats = optimizer.get_statistics()
                tuner.data_logger.log_statistics(stats)
                logger.info(f"Final stats for {stats['coefficient_name']}: {stats}")
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
