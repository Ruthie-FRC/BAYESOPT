"""
Main tuner coordinator module.

This module coordinates all tuner components and runs the tuning loop
in a background thread with safe startup/shutdown.
"""

import time
import threading
import logging
from typing import Optional, Dict

import keyboard

from .config import TunerConfig
from .nt_interface import NetworkTablesInterface, ShotData
from .optimizer import CoefficientTuner
from .logger import TunerLogger, setup_logging


logger = logging.getLogger(__name__)

# Keyboard shortcut to stop the tuner
STOP_HOTKEY = 'ctrl+shift+x'


class BayesianTunerCoordinator:
    """
    Main coordinator for the Bayesian tuner system.
    
    Manages the tuning loop, coordinates between NT interface, optimizer,
    and logger, and handles safe startup/shutdown.
    
    Supports two optimization modes:
    - MANUAL (autotune OFF): Accumulates shots, waits for dashboard button press
    - AUTOMATIC (autotune ON): Automatically optimizes after reaching shot threshold
    
    Attributes:
        config: TunerConfig with all settings
        nt_interface: NetworkTables communication handler
        optimizer: Bayesian optimization engine
        data_logger: CSV logging for analysis
        accumulated_shots: List of shots waiting to be processed
        current_coefficient_values: Current values of all coefficients
    """
    
    def __init__(self, config: Optional[TunerConfig] = None):
        """
        Initialize tuner coordinator.
        
        Args:
            config: TunerConfig object. If None, uses default config from files.
        """
        self.config = config or TunerConfig()
        
        # Validate configuration
        warnings = self.config.validate_config()
        if warnings:
            logger.warning(f"Configuration warnings: {warnings}")
        
        # ── Core Components ──
        self.nt_interface = NetworkTablesInterface(self.config)
        self.optimizer = CoefficientTuner(self.config)
        self.data_logger = TunerLogger(self.config)
        
        # ── Runtime State ──
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_shot_timestamp = 0.0
        
        # ── Runtime Enable/Disable Toggle ──
        # This can be changed at runtime via dashboard
        self.runtime_enabled = self.config.TUNER_ENABLED
        
        # ── Coefficient Tracking ──
        # Current values of all coefficients being tuned
        self.current_coefficient_values: Dict[str, float] = {}
        
        # ── Autotune Shot Accumulation ──
        # Shots are collected here until optimization is triggered
        # Each entry is {'shot_data': ShotData, 'coefficient_values': dict}
        self.accumulated_shots: list = []
        
        # Log startup info
        logger.info("Bayesian Tuner Coordinator initialized")
        logger.info(f"Autotune mode: {'AUTOMATIC' if self.config.AUTOTUNE_ENABLED else 'MANUAL'}")
        if self.config.AUTOTUNE_ENABLED:
            logger.info(f"Auto-optimization will run after {self.config.AUTOTUNE_SHOT_THRESHOLD} shots")
        else:
            logger.info("Press 'Run Optimization' button on dashboard to trigger optimization")
    
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
        
        # Start NetworkTables connection
        if not self.nt_interface.start(server_ip):
            logger.error("Failed to start NetworkTables, tuner not started")
            self.data_logger.log_event('ERROR', 'Failed to start NT')
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
        
        # Initialize autotune dashboard controls (creates the button on dashboard)
        self.nt_interface.write_autotune_status(
            self.config.AUTOTUNE_ENABLED,
            len(self.accumulated_shots),
            self.config.AUTOTUNE_SHOT_THRESHOLD
        )
        logger.info(f"Dashboard controls initialized: autotune={'ON' if self.config.AUTOTUNE_ENABLED else 'OFF'}, "
                   f"threshold={self.config.AUTOTUNE_SHOT_THRESHOLD}")
        
        # Initialize manual coefficient controls for real-time adjustment from laptop
        self.nt_interface.initialize_manual_controls(self.config.COEFFICIENTS)
        logger.info("Manual coefficient adjustment controls initialized")
        
        # Initialize fine-tuning mode controls
        self.nt_interface.initialize_fine_tuning_controls()
        logger.info("Fine-tuning mode controls initialized")
        
        # Initialize backtrack controls
        self.nt_interface.initialize_backtrack_controls(self.config.TUNING_ORDER)
        logger.info("Backtrack tuning controls initialized")
        
        # Log initial coefficient combination
        self.data_logger.log_coefficient_combination(
            self.current_coefficient_values,
            event="SESSION_START"
        )
        
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
        
        # Stop NetworkTables connection
        self.nt_interface.stop()
        
        # Close logger
        self.data_logger.close()
        
        logger.info("Tuner stopped")
    
    def _tuning_loop(self):
        """Main tuning loop that runs in background thread."""
        logger.info("Tuning loop started")
        
        update_period = 1.0 / self.config.TUNER_UPDATE_RATE_HZ
        
        while self.running:
            try:
                # Check for runtime enable/disable toggle from dashboard
                self._check_runtime_toggle()
                
                # Check for safety conditions (includes runtime_enabled check)
                if not self._check_safety_conditions():
                    # Update status to show paused/disabled state
                    self.nt_interface.write_tuner_enabled_status(
                        self.runtime_enabled,
                        paused=not self.runtime_enabled or self.nt_interface.is_match_mode()
                    )
                    time.sleep(1.0)
                    continue
                
                # ── MANUAL COEFFICIENT ADJUSTMENT ──
                # Allows real-time coefficient changes from dashboard/laptop
                self._check_manual_coefficient_adjustment()
                
                # ── BACKTRACK TUNING ──
                # Allows going back to previously tuned coefficients
                self._check_backtrack_request()
                
                # Check for new shot data
                shot_data = self.nt_interface.read_shot_data()
                
                if shot_data:
                    self._accumulate_shot(shot_data)
                
                # Check for skip to next coefficient button
                # Only process if auto-advance is DISABLED for current coefficient
                if not self._get_current_auto_advance():
                    if self.nt_interface.read_skip_to_next_button():
                        self._skip_to_next_coefficient()
                
                # Check for runtime shot threshold updates (global and local)
                self._check_threshold_updates()
                
                # Check for auto-advance (works independently of autotune mode)
                # This allows advancing to next coefficient on 100% success even in manual mode
                self._check_auto_advance()
                
                # Check if we should run optimization based on autotune mode
                should_optimize = self._check_optimization_trigger()
                
                if should_optimize:
                    self._run_optimization()
                
                # Update status on dashboard
                self._update_status()
                
                # Sleep until next update
                time.sleep(update_period)
                
            except Exception as e:
                logger.error(f"Error in tuning loop: {e}", exc_info=True)
                time.sleep(1.0)
        
        logger.info("Tuning loop ended")
    
    def _check_runtime_toggle(self):
        """
        Check for runtime enable/disable toggle changes from the dashboard.
        
        This allows drivers to enable or disable the entire BayesOpt tuner
        at runtime via the dashboard, without needing to restart the program.
        
        When disabled:
        - No shots are accumulated
        - No optimization runs
        - Dashboard shows "Tuner Disabled" status
        
        When re-enabled:
        - Tuner resumes from where it left off
        - Accumulated shots are preserved (if any)
        """
        was_changed, new_value = self.nt_interface.read_tuner_enabled_toggle()
        
        if was_changed:
            old_value = self.runtime_enabled
            self.runtime_enabled = new_value
            
            old_state = "ENABLED" if old_value else "DISABLED"
            new_state = "ENABLED" if new_value else "DISABLED"
            
            if new_value:
                logger.info(f"Tuner state changed: {old_state} -> {new_state}")
                self.data_logger.log_event('ENABLE', f'Tuner enabled via dashboard (was {old_state})')
            else:
                logger.info(f"Tuner state changed: {old_state} -> {new_state}")
                self.data_logger.log_event('DISABLE', f'Tuner disabled via dashboard (was {old_state})')
    
    def _check_safety_conditions(self) -> bool:
        """
        Check safety conditions before continuing tuning.
        
        Returns:
            True if safe to continue, False otherwise
        """
        # Check if tuner is disabled at runtime
        if not self.runtime_enabled:
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
    
    def _accumulate_shot(self, shot_data: ShotData):
        """
        Accumulate a shot for later optimization.
        
        This is the core of the autotune feature. Instead of processing shots
        immediately (which would adjust coefficients after every shot), we
        collect them here until optimization is triggered.
        
        Shots are stored with their corresponding coefficient values so the
        optimizer knows what settings were used when each shot was taken.
        
        When optimization is triggered (by button press or shot threshold),
        all accumulated shots are processed together as a batch.
        
        Args:
            shot_data: ShotData object containing hit/miss and trajectory info
        """
        logger.info(f"Accumulating shot: hit={shot_data.hit}, distance={shot_data.distance:.2f}m")
        
        # Store shot with current coefficient values
        # We need to copy the dict so changes don't affect stored data
        self.accumulated_shots.append({
            'shot_data': shot_data,
            'coefficient_values': self.current_coefficient_values.copy()
        })
        
        # Log to CSV for offline analysis
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
            tuner_status=f"Collecting shots: {len(self.accumulated_shots)}/{self.config.AUTOTUNE_SHOT_THRESHOLD}",
            all_coefficient_values=self.current_coefficient_values,
        )
        
        logger.info(f"Shots accumulated: {len(self.accumulated_shots)}/{self.config.AUTOTUNE_SHOT_THRESHOLD}")
    
    def _check_optimization_trigger(self) -> bool:
        """
        Check if optimization should be triggered based on autotune mode.
        
        This implements the two autotune modes, respecting per-coefficient overrides:
        
        MANUAL MODE (autotune_enabled = False):
            - Checks if the "Run Optimization" button was pressed on dashboard
            - If pressed, returns True to trigger optimization
            - Allows drivers to control exactly when tuning happens
        
        AUTOMATIC MODE (autotune_enabled = True):
            - Checks if accumulated shots >= autotune_shot_threshold
            - If threshold reached, returns True to trigger optimization
            - Fully automatic tuning without driver intervention
        
        Returns:
            True if optimization should run now, False otherwise
        """
        # No shots accumulated, nothing to optimize
        if len(self.accumulated_shots) == 0:
            return False
        
        # Get the effective autotune settings for the current coefficient
        current_autotune, current_threshold = self._get_current_autotune_settings()
        
        if current_autotune:
            # ── AUTOMATIC MODE ──
            # Check if we've collected enough shots (reached sample size)
            if len(self.accumulated_shots) >= current_threshold:
                logger.info(f"Autotune triggered: reached sample size of {current_threshold} shots")
                return True
        else:
            # ── MANUAL MODE ──
            # Check if the dashboard button was pressed
            if self.nt_interface.read_run_optimization_button():
                logger.info(f"Manual optimization triggered: processing {len(self.accumulated_shots)} accumulated shots")
                return True
        
        return False
    
    def _get_current_autotune_settings(self) -> tuple:
        """
        Get the effective autotune settings for the current coefficient.
        
        Returns:
            Tuple of (autotune_enabled, shot_threshold) for current coefficient
        """
        coeff_name = self.optimizer.get_current_coefficient_name()
        if coeff_name and coeff_name in self.config.COEFFICIENTS:
            coeff = self.config.COEFFICIENTS[coeff_name]
            return coeff.get_effective_autotune_settings(
                self.config.AUTOTUNE_ENABLED,
                self.config.AUTOTUNE_SHOT_THRESHOLD,
                self.config.AUTOTUNE_FORCE_GLOBAL
            )
        # Fallback to global settings
        return (self.config.AUTOTUNE_ENABLED, self.config.AUTOTUNE_SHOT_THRESHOLD)
    
    def _get_current_auto_advance(self) -> bool:
        """
        Get the effective auto-advance enabled setting for the current coefficient.
        
        Returns:
            Whether auto-advance is enabled for current coefficient
        """
        coeff_name = self.optimizer.get_current_coefficient_name()
        if coeff_name and coeff_name in self.config.COEFFICIENTS:
            coeff = self.config.COEFFICIENTS[coeff_name]
            return coeff.get_effective_auto_advance(
                self.config.AUTO_ADVANCE_ON_SUCCESS,
                self.config.AUTO_ADVANCE_FORCE_GLOBAL
            )
        return self.config.AUTO_ADVANCE_ON_SUCCESS
    
    def _get_current_auto_advance_settings(self) -> tuple:
        """
        Get the effective auto-advance settings for the current coefficient.
        
        Returns:
            Tuple of (auto_advance_enabled, shot_threshold) for current coefficient
        """
        coeff_name = self.optimizer.get_current_coefficient_name()
        if coeff_name and coeff_name in self.config.COEFFICIENTS:
            coeff = self.config.COEFFICIENTS[coeff_name]
            return coeff.get_effective_auto_advance_settings(
                self.config.AUTO_ADVANCE_ON_SUCCESS,
                self.config.AUTO_ADVANCE_SHOT_THRESHOLD,
                self.config.AUTO_ADVANCE_FORCE_GLOBAL
            )
        # Fallback to global settings
        return (self.config.AUTO_ADVANCE_ON_SUCCESS, self.config.AUTO_ADVANCE_SHOT_THRESHOLD)
    
    def _check_auto_advance(self):
        """
        Check if we should auto-advance to the next coefficient.
        
        Auto-advance works INDEPENDENTLY of autotune mode:
        - Uses its OWN shot threshold (separate from autotune threshold)
        - If accumulated shots >= auto_advance_threshold AND all shots are hits → advance
        - Works in both autotune ON and OFF modes
        """
        # Get current auto-advance settings (enabled + threshold)
        auto_advance_enabled, auto_advance_threshold = self._get_current_auto_advance_settings()
        
        # Only check if auto-advance is enabled for current coefficient
        if not auto_advance_enabled:
            return
        
        # Check if we've reached the auto-advance threshold
        if len(self.accumulated_shots) < auto_advance_threshold:
            return
        
        # Check if all shots are hits (100% success rate)
        hits = sum(1 for s in self.accumulated_shots if s['shot_data'].hit)
        total = len(self.accumulated_shots)
        
        if hits == total and total > 0:
            logger.info(f"Auto-advance triggered: 100% success rate ({hits}/{total} hits) over threshold of {auto_advance_threshold}")
            self.data_logger.log_event('AUTO_ADVANCE', f'100% success rate over {auto_advance_threshold} shots, advancing to next coefficient')
            
            # Clear accumulated shots and advance
            self.accumulated_shots = []
            if self.optimizer.current_optimizer:
                self.optimizer.advance_to_next_coefficient()
            
            logger.info(f"Now tuning: {self.optimizer.get_current_coefficient_name()}")
    
    def _skip_to_next_coefficient(self):
        """Skip to the next coefficient in the tuning order."""
        logger.info("Skipping to next coefficient...")
        self.data_logger.log_event('SKIP', 'Manually skipped to next coefficient')
        
        # Clear accumulated shots
        self.accumulated_shots = []
        
        # Tell the optimizer to move to the next coefficient
        if self.optimizer.current_optimizer:
            self.optimizer.advance_to_next_coefficient()
        
        logger.info(f"Now tuning: {self.optimizer.get_current_coefficient_name()}")
    
    def _check_threshold_updates(self):
        """
        Check for runtime threshold updates from dashboard.
        
        Handles two types of updates:
        1. Global threshold - changes default for all coefficients without override
        2. Local threshold - changes threshold for current coefficient only
        """
        # Check for global threshold update
        new_global = self.nt_interface.read_global_threshold_update()
        if new_global > 0:
            self._update_global_threshold(new_global)
        
        # Check for local threshold update (current coefficient only)
        new_local = self.nt_interface.read_local_threshold_update()
        if new_local > 0:
            self._update_local_threshold(new_local)
    
    def _update_global_threshold(self, new_threshold: int):
        """
        Update the GLOBAL shot threshold at runtime.
        
        This changes the default threshold used by all coefficients
        that don't have their own override.
        
        Args:
            new_threshold: New global shot threshold value
        """
        old_threshold = self.config.AUTOTUNE_SHOT_THRESHOLD
        logger.info(f"Updating GLOBAL shot threshold: {old_threshold} -> {new_threshold}")
        self.config.AUTOTUNE_SHOT_THRESHOLD = new_threshold
        self.data_logger.log_event('GLOBAL_THRESHOLD_UPDATE', f'Global threshold: {old_threshold} -> {new_threshold}')
    
    def _update_local_threshold(self, new_threshold: int):
        """
        Update the LOCAL shot threshold for current coefficient at runtime.
        
        This changes the threshold for ONLY the current coefficient,
        enabling its autotune_override so the local setting takes effect.
        
        Args:
            new_threshold: New local shot threshold value
        """
        coeff_name = self.optimizer.get_current_coefficient_name()
        if not coeff_name or coeff_name not in self.config.COEFFICIENTS:
            logger.warning(f"Cannot update local threshold: no current coefficient")
            return
        
        coeff = self.config.COEFFICIENTS[coeff_name]
        # Get the current effective threshold for proper logging
        _, old_threshold = coeff.get_effective_autotune_settings(
            self.config.AUTOTUNE_ENABLED, 
            self.config.AUTOTUNE_SHOT_THRESHOLD
        )
        
        # Enable override so local setting takes precedence
        coeff.autotune_override = True
        coeff.autotune_shot_threshold = new_threshold
        
        logger.info(f"Updating LOCAL shot threshold for {coeff_name}: {old_threshold} -> {new_threshold}")
        self.data_logger.log_event('LOCAL_THRESHOLD_UPDATE', f'{coeff_name} threshold: {old_threshold} -> {new_threshold}')
    
    def _run_optimization(self):
        """
        Run the optimization algorithm on accumulated shots and update coefficients.
        
        This is called when optimization is triggered (either by button press
        in manual mode, or by reaching shot threshold in automatic mode).
        
        Process:
        1. Log the optimization event
        2. Feed all accumulated shots to the optimizer
        3. Check for 100% success rate (for auto-advance feature)
        4. Clear the accumulated shots (start fresh for next batch)
        5. Get the optimizer's suggested coefficient updates
        6. Write new coefficient values to NetworkTables
        7. If auto-advance enabled and 100% success, move to next coefficient
        8. Update dashboard status
        
        The optimizer uses Bayesian optimization to find the best coefficient
        values based on the hit/miss results of the accumulated shots.
        """
        # Defensive check - normally _check_optimization_trigger prevents this,
        # but this protects against direct method calls
        if len(self.accumulated_shots) == 0:
            logger.debug("No shots to optimize (this is expected if called directly)")
            return
        
        logger.info(f"Running optimization on {len(self.accumulated_shots)} accumulated shots")
        self.data_logger.log_event('OPTIMIZATION', f'Running optimization on {len(self.accumulated_shots)} shots')
        
        # Process all accumulated shots through the optimizer
        for shot_record in self.accumulated_shots:
            shot_data = shot_record['shot_data']
            coeff_values = shot_record['coefficient_values']
            self.optimizer.record_shot(shot_data, coeff_values)
        
        # Clear accumulated shots
        self.accumulated_shots = []
        
        # Get and apply coefficient updates
        self._update_coefficients()
        
        # NOTE: Auto-advance is now handled separately in _check_auto_advance()
        # This allows auto-advance to work independently of autotune mode
        
        # Get current settings for dashboard update
        current_autotune, current_threshold = self._get_current_autotune_settings()
        
        # Update dashboard status
        self.nt_interface.write_autotune_status(
            current_autotune,
            len(self.accumulated_shots),
            current_threshold
        )
        
        logger.info("Optimization complete, coefficients updated")
    
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
                
                # Log the new coefficient combination with timestamp
                self.data_logger.log_coefficient_combination(
                    self.current_coefficient_values,
                    event="OPTIMIZATION"
                )
                
                # Signal interlock system that coefficients are updated
                self.nt_interface.signal_coefficients_updated()
            else:
                logger.error(f"Failed to write {coeff_name} to NT")
    
    def _update_status(self):
        """Update tuner status in NetworkTables for driver feedback."""
        # Get per-coefficient settings
        current_autotune, current_threshold = self._get_current_autotune_settings()
        current_auto_advance = self._get_current_auto_advance()
        
        # Build status based on current coefficient's autotune mode
        shot_count = len(self.accumulated_shots)
        coeff_name = self.optimizer.get_current_coefficient_name() or "None"
        
        if current_autotune:
            status = f"Autotune ON: {shot_count}/{current_threshold} shots"
        else:
            status = f"Manual mode: {shot_count} shots (press button to optimize)"
        
        # Add optimizer info if available
        if self.optimizer.current_optimizer:
            step_size = self.optimizer.current_optimizer.current_step_size
            status += f" | Tuning: {coeff_name} (step: {step_size:.6f})"
        
        self.nt_interface.write_status(status)
        
        # Update autotune dashboard values with current coefficient's settings
        self.nt_interface.write_autotune_status(
            current_autotune,
            shot_count,
            current_threshold
        )
        
        # Update current coefficient info on dashboard
        self.nt_interface.write_current_coefficient_info(
            coeff_name,
            current_autotune,
            current_threshold,
            current_auto_advance
        )
        
        # Update tuner enabled status on dashboard
        self.nt_interface.write_tuner_enabled_status(
            self.runtime_enabled,
            paused=self.nt_interface.is_match_mode()
        )
        
        # ── UPDATE ALL COEFFICIENT VALUES TO DASHBOARD ──
        # This allows drivers to see current operating values vs code defaults
        self.nt_interface.write_all_coefficient_values_to_dashboard(
            self.current_coefficient_values,
            self.config.COEFFICIENTS
        )
        
        # ── UPDATE BACKTRACK STATUS ──
        # Show which coefficients have been tuned and can be backtracked to
        tuned_names = [opt.coeff_config.name for opt in self.optimizer.completed_coefficients]
        current_name = self.optimizer.get_current_coefficient_name() or "None"
        self.nt_interface.write_backtrack_status(tuned_names, current_name)
    
    def _check_manual_coefficient_adjustment(self):
        """
        Check for and apply manual coefficient adjustment from dashboard.
        
        This allows drivers/programmers to manually set any coefficient value
        in real-time from the laptop/dashboard without waiting for optimization.
        
        Useful for:
        - Quick testing of specific coefficient values
        - Resetting a coefficient to a known good value
        - Fine-tuning after optimization is complete
        
        Dashboard Location: /Tuning/BayesianTuner/ManualControl/
        """
        triggered, coeff_name, new_value = self.nt_interface.read_manual_coefficient_adjustment()
        
        if triggered and coeff_name:
            # Validate coefficient exists
            if coeff_name not in self.config.COEFFICIENTS:
                logger.warning(f"Manual adjustment: unknown coefficient '{coeff_name}'")
                return
            
            coeff_config = self.config.COEFFICIENTS[coeff_name]
            
            # Clamp value to valid range
            clamped_value = coeff_config.clamp(new_value)
            if clamped_value != new_value:
                logger.warning(f"Manual value {new_value} clamped to {clamped_value} for {coeff_name}")
            
            # Write to NetworkTables
            success = self.nt_interface.write_coefficient(coeff_config.nt_key, clamped_value, force=True)
            
            if success:
                old_value = self.current_coefficient_values.get(coeff_name, coeff_config.default_value)
                self.current_coefficient_values[coeff_name] = clamped_value
                
                logger.info(f"Manual coefficient adjustment: {coeff_name} = {old_value:.6f} -> {clamped_value:.6f}")
                self.data_logger.log_event('MANUAL_ADJUST', f'{coeff_name}: {old_value:.6f} -> {clamped_value:.6f}')
                
                # Log the new coefficient combination
                self.data_logger.log_coefficient_combination(
                    self.current_coefficient_values,
                    event="MANUAL_CHANGE"
                )
                
                # Signal interlock system
                self.nt_interface.signal_coefficients_updated()
            else:
                logger.error(f"Failed to apply manual adjustment for {coeff_name}")
    
    def _check_backtrack_request(self):
        """
        Check for and handle backtrack tuning request from dashboard.
        
        Backtracking allows the tuner to go back to a previously tuned
        coefficient if inaccuracy is being caused by improper earlier tuning.
        
        When triggered:
        1. Resets the optimizer to the specified coefficient
        2. Clears accumulated shots
        3. Logs the backtrack event
        
        Dashboard Location: /Tuning/BayesianTuner/Backtrack/
        """
        triggered, target_coeff = self.nt_interface.read_backtrack_request()
        
        if triggered and target_coeff:
            # Validate coefficient exists and is in tuning order
            if target_coeff not in self.config.COEFFICIENTS:
                logger.warning(f"Backtrack: unknown coefficient '{target_coeff}'")
                return
            
            if target_coeff not in self.config.TUNING_ORDER:
                logger.warning(f"Backtrack: coefficient '{target_coeff}' not in tuning order")
                return
            
            # Find the index of the target coefficient
            try:
                target_index = self.config.TUNING_ORDER.index(target_coeff)
            except ValueError:
                logger.error(f"Backtrack: could not find index for '{target_coeff}'")
                return
            
            # Current coefficient info
            current_coeff = self.optimizer.get_current_coefficient_name() or "None"
            
            logger.info(f"Backtracking from {current_coeff} to {target_coeff}")
            self.data_logger.log_event('BACKTRACK', f'From {current_coeff} to {target_coeff}')
            
            # Log coefficient interaction (potential issue detected)
            self.data_logger.log_coefficient_interaction(
                current_coeff,
                target_coeff,
                "BACKTRACK",
                f"User requested backtrack - possible interaction issue"
            )
            
            # Reset optimizer to target coefficient
            self.optimizer.current_index = target_index
            self.optimizer._start_next_coefficient()
            
            # Clear accumulated shots
            self.accumulated_shots = []
            
            # Log the backtrack
            self.data_logger.log_coefficient_combination(
                self.current_coefficient_values,
                event="BACKTRACK"
            )
            
            logger.info(f"Backtrack complete, now tuning: {self.optimizer.get_current_coefficient_name()}")
    
    def get_accumulated_shots_count(self) -> int:
        """
        Get the number of accumulated shots waiting to be processed.
        
        Returns:
            Number of accumulated shots
        """
        return len(self.accumulated_shots)
    
    def get_current_autotune_settings(self) -> tuple:
        """
        Get the effective autotune settings for the current coefficient.
        
        This is a public accessor for the internal _get_current_autotune_settings method.
        
        Returns:
            Tuple of (autotune_enabled, shot_threshold) for current coefficient
        """
        return self._get_current_autotune_settings()
    
    def get_status(self) -> Dict:
        """
        Get current tuner status.
        
        Returns:
            Dict with status information
        """
        status = {
            'running': self.running,
            'enabled': self.config.TUNER_ENABLED,
            'runtime_enabled': self.runtime_enabled,  # Runtime toggle status
            'autotune_enabled': self.config.AUTOTUNE_ENABLED,
            'autotune_shot_threshold': self.config.AUTOTUNE_SHOT_THRESHOLD,
            'accumulated_shots': len(self.accumulated_shots),
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
        # Flag to track if the user wants to stop
        stop_requested = threading.Event()
        hotkey_registered = False
        
        def on_stop_shortcut():
            """Callback when stop hotkey is pressed."""
            logger.info(f"Stop shortcut ({STOP_HOTKEY}) pressed")
            stop_requested.set()
        
        # Register the keyboard shortcut
        try:
            keyboard.add_hotkey(STOP_HOTKEY, on_stop_shortcut)
            hotkey_registered = True
        except Exception as e:
            logger.warning(f"Failed to register {STOP_HOTKEY} hotkey: {e}")
            logger.info("Falling back to Ctrl+C to stop the tuner")
        
        try:
            if hotkey_registered:
                logger.info(f"Tuner running. Press {STOP_HOTKEY} to stop.")
            else:
                logger.info("Tuner running. Press Ctrl+C to stop.")
            
            # Keep running until interrupted or tuning complete
            while not tuner.optimizer.is_complete() and not stop_requested.is_set():
                time.sleep(1.0)
                
                # Print periodic status
                status = tuner.get_status()
                if status['running']:
                    logger.info(f"Status: {status['tuning_status']}")
            
            if stop_requested.is_set():
                logger.info("Interrupted by user")
            else:
                logger.info("Tuning complete!")
            
            # Log final statistics
            for optimizer in tuner.optimizer.completed_coefficients:
                stats = optimizer.get_statistics()
                tuner.data_logger.log_statistics(stats)
                logger.info(f"Final stats for {stats['coefficient_name']}: {stats}")
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user (Ctrl+C)")
        finally:
            # Clean up the keyboard hook if it was registered
            if hotkey_registered:
                try:
                    keyboard.remove_hotkey(STOP_HOTKEY)
                except Exception:
                    pass

