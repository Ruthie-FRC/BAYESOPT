"""
Bayesian optimizer module for coefficient tuning.

This module implements Bayesian optimization using scikit-optimize to tune
shooting coefficients based on hit/miss feedback with adaptive step sizes.
"""

import logging
from typing import List, Tuple, Optional, Dict
import numpy as np

try:
    from skopt import Optimizer
    from skopt.space import Real, Integer
except ImportError:
    # Provide mock for testing without scikit-optimize
    class Optimizer:
        def __init__(self, *args, **kwargs):
            pass
        
        def ask(self):
            return [0.5]
        
        def tell(self, x, y):
            pass
    
    class Real:
        def __init__(self, *args, **kwargs):
            pass
    
    class Integer:
        def __init__(self, *args, **kwargs):
            pass


logger = logging.getLogger(__name__)


class BayesianOptimizer:
    """
    Bayesian optimizer for a single coefficient.
    
    Uses Expected Improvement acquisition function and Gaussian Process
    to efficiently explore the parameter space.
    """
    
    def __init__(self, coeff_config, tuner_config):
        """
        Initialize optimizer for a specific coefficient.
        
        Args:
            coeff_config: CoefficientConfig object
            tuner_config: TunerConfig object
        """
        self.coeff_config = coeff_config
        self.tuner_config = tuner_config
        
        # Create search space
        if coeff_config.is_integer:
            self.search_space = [Integer(
                int(coeff_config.min_value),
                int(coeff_config.max_value),
                name=coeff_config.name
            )]
        else:
            self.search_space = [Real(
                coeff_config.min_value,
                coeff_config.max_value,
                name=coeff_config.name
            )]
        
        # Initialize optimizer
        self.optimizer = Optimizer(
            dimensions=self.search_space,
            n_initial_points=tuner_config.N_INITIAL_POINTS,
            acq_func=tuner_config.ACQUISITION_FUNCTION,
            random_state=None,  # Use random seed for exploration
        )
        
        # Tracking
        self.iteration = 0
        self.current_step_size = coeff_config.initial_step_size
        self.best_value = coeff_config.default_value
        self.best_score = float('-inf')
        self.evaluation_history = []
        
        logger.info(f"Initialized optimizer for {coeff_config.name}")
    
    def suggest_next_value(self) -> float:
        """
        Suggest next coefficient value to try.
        
        Returns:
            Suggested coefficient value
        """
        try:
            # Get next point from optimizer
            suggested = self.optimizer.ask()
            value = suggested[0]
            
            # Apply step size decay if enabled
            if self.tuner_config.STEP_SIZE_DECAY_ENABLED and self.iteration > 0:
                # Calculate decayed step size
                decay_factor = self.coeff_config.step_decay_rate ** self.iteration
                min_step = self.coeff_config.initial_step_size * self.tuner_config.MIN_STEP_SIZE_RATIO
                self.current_step_size = max(
                    min_step,
                    self.coeff_config.initial_step_size * decay_factor
                )
            
            # Clamp to valid range
            value = self.coeff_config.clamp(value)
            
            logger.info(f"Suggesting {self.coeff_config.name} = {value:.6f} (step size: {self.current_step_size:.6f})")
            return value
            
        except Exception as e:
            logger.error(f"Error suggesting next value: {e}")
            return self.coeff_config.default_value
    
    def report_result(self, value: float, hit: bool, additional_data: Optional[Dict] = None):
        """
        Report the result of testing a coefficient value.
        
        Args:
            value: The coefficient value that was tested
            hit: Whether the shot hit (True) or missed (False)
            additional_data: Optional dict with distance, velocity, etc.
        """
        try:
            # Convert hit/miss to optimization score (maximize hit rate)
            # Score is 1.0 for hit, -1.0 for miss
            score = 1.0 if hit else -1.0
            
            # Add small bonus for being closer to target if distance data available
            if additional_data and 'distance' in additional_data:
                # Smaller distances are slightly better (secondary objective)
                distance = additional_data.get('distance', 0)
                if distance > 0:
                    distance_bonus = -0.01 / max(distance, 1.0)  # Small negative bonus
                    score += distance_bonus
            
            # Tell optimizer the result
            self.optimizer.tell([value], score)
            
            # Track best result
            if score > self.best_score:
                self.best_score = score
                self.best_value = value
                logger.info(f"New best for {self.coeff_config.name}: {value:.6f} (score: {score:.3f})")
            
            # Record in history
            self.evaluation_history.append({
                'iteration': self.iteration,
                'value': value,
                'hit': hit,
                'score': score,
                'step_size': self.current_step_size,
                'additional_data': additional_data or {}
            })
            
            self.iteration += 1
            
            logger.debug(f"Reported result: {self.coeff_config.name}={value:.6f}, hit={hit}, score={score:.3f}")
            
        except Exception as e:
            logger.error(f"Error reporting result: {e}")
    
    def is_converged(self) -> bool:
        """
        Check if optimization has converged.
        
        Returns:
            True if converged or max iterations reached
        """
        # Check if we've reached max iterations
        if self.iteration >= self.tuner_config.N_CALLS_PER_COEFFICIENT:
            logger.info(f"{self.coeff_config.name} reached max iterations ({self.iteration})")
            return True
        
        # Check if step size is below minimum (indicates convergence)
        min_step = self.coeff_config.initial_step_size * self.tuner_config.MIN_STEP_SIZE_RATIO
        if self.current_step_size <= min_step * 1.1:  # Small tolerance
            logger.info(f"{self.coeff_config.name} converged (step size: {self.current_step_size:.6f})")
            return True
        
        # Check if we have enough history to evaluate convergence
        if len(self.evaluation_history) >= 5:
            # Check variance in recent scores
            recent_scores = [h['score'] for h in self.evaluation_history[-5:]]
            variance = np.var(recent_scores)
            
            # If variance is very low, we've converged
            if variance < 0.01:
                logger.info(f"{self.coeff_config.name} converged (low variance: {variance:.6f})")
                return True
        
        return False
    
    def get_best_value(self) -> float:
        """
        Get the best coefficient value found so far.
        
        Returns:
            Best coefficient value
        """
        return self.best_value
    
    def get_statistics(self) -> Dict:
        """
        Get optimization statistics.
        
        Returns:
            Dict with statistics (iterations, best value, convergence, etc.)
        """
        hit_rate = 0.0
        if self.evaluation_history:
            hits = sum(1 for h in self.evaluation_history if h['hit'])
            hit_rate = hits / len(self.evaluation_history)
        
        return {
            'coefficient_name': self.coeff_config.name,
            'iterations': self.iteration,
            'best_value': self.best_value,
            'best_score': self.best_score,
            'current_step_size': self.current_step_size,
            'hit_rate': hit_rate,
            'is_converged': self.is_converged(),
            'total_evaluations': len(self.evaluation_history),
        }


class CoefficientTuner:
    """
    Manages sequential tuning of multiple coefficients.
    
    Tunes one coefficient at a time in the specified priority order,
    moving to the next when the current one converges.
    """
    
    def __init__(self, tuner_config):
        """
        Initialize coefficient tuner.
        
        Args:
            tuner_config: TunerConfig object
        """
        self.config = tuner_config
        self.coefficients = tuner_config.get_enabled_coefficients_in_order()
        
        self.current_index = 0
        self.current_optimizer: Optional[BayesianOptimizer] = None
        self.completed_coefficients = []
        
        # Shot accumulation for validation
        self.pending_shots = []
        self.consecutive_invalid_shots = 0
        
        logger.info(f"Initialized tuner for {len(self.coefficients)} coefficients")
        
        # Start with first coefficient
        if self.coefficients:
            self._start_next_coefficient()
    
    def _start_next_coefficient(self):
        """Start optimizing the next coefficient in the sequence."""
        if self.current_index >= len(self.coefficients):
            logger.info("All coefficients tuned!")
            self.current_optimizer = None
            return
        
        coeff = self.coefficients[self.current_index]
        logger.info(f"Starting optimization for {coeff.name} ({self.current_index + 1}/{len(self.coefficients)})")
        
        self.current_optimizer = BayesianOptimizer(coeff, self.config)
        self.pending_shots = []
    
    def get_current_coefficient_name(self) -> Optional[str]:
        """Get name of coefficient currently being tuned."""
        if self.current_optimizer:
            return self.current_optimizer.coeff_config.name
        return None
    
    def suggest_coefficient_update(self) -> Optional[Tuple[str, float]]:
        """
        Suggest next coefficient value to test.
        
        Returns:
            Tuple of (coefficient_name, suggested_value) or None if done
        """
        if not self.current_optimizer:
            return None
        
        value = self.current_optimizer.suggest_next_value()
        name = self.current_optimizer.coeff_config.name
        
        return (name, value)
    
    def record_shot(self, shot_data, coefficient_values: Dict[str, float]):
        """
        Record a shot result for the current coefficient being tuned.
        
        Args:
            shot_data: ShotData object
            coefficient_values: Current values of all coefficients
        """
        if not self.current_optimizer:
            logger.warning("No active optimizer to record shot")
            return
        
        # Validate shot data
        if not shot_data.is_valid():
            self.consecutive_invalid_shots += 1
            logger.warning(f"Invalid shot data (consecutive: {self.consecutive_invalid_shots})")
            
            if self.consecutive_invalid_shots >= self.config.MAX_CONSECUTIVE_INVALID_SHOTS:
                logger.error("Too many consecutive invalid shots, stopping tuning")
                self.current_optimizer = None
            return
        
        # Reset invalid counter
        self.consecutive_invalid_shots = 0
        
        # Get current coefficient value
        coeff_name = self.current_optimizer.coeff_config.name
        current_value = coefficient_values.get(coeff_name, self.current_optimizer.coeff_config.default_value)
        
        # Add to pending shots
        self.pending_shots.append({
            'shot_data': shot_data,
            'coefficient_value': current_value,
        })
        
        # Check if we have enough shots to report
        if len(self.pending_shots) >= self.config.MIN_VALID_SHOTS_BEFORE_UPDATE:
            self._process_pending_shots()
    
    def _process_pending_shots(self):
        """Process accumulated shots and report to optimizer."""
        if not self.pending_shots or not self.current_optimizer:
            return
        
        # Aggregate shots - use majority vote for hit/miss
        hits = sum(1 for s in self.pending_shots if s['shot_data'].hit)
        hit = hits > len(self.pending_shots) / 2
        
        # Use average coefficient value
        avg_value = np.mean([s['coefficient_value'] for s in self.pending_shots])
        
        # Average distance
        avg_distance = np.mean([s['shot_data'].distance for s in self.pending_shots])
        
        # Report to optimizer
        additional_data = {
            'distance': avg_distance,
            'num_shots': len(self.pending_shots),
            'hit_rate': hits / len(self.pending_shots),
        }
        
        self.current_optimizer.report_result(avg_value, hit, additional_data)
        
        # Clear pending shots
        self.pending_shots = []
        
        # Check for convergence
        if self.current_optimizer.is_converged():
            stats = self.current_optimizer.get_statistics()
            logger.info(f"Coefficient {stats['coefficient_name']} converged: best={stats['best_value']:.6f}, hit_rate={stats['hit_rate']:.2%}")
            
            self.completed_coefficients.append(self.current_optimizer)
            self.current_index += 1
            self._start_next_coefficient()
    
    def is_complete(self) -> bool:
        """Check if all coefficients have been tuned."""
        return self.current_optimizer is None and self.current_index >= len(self.coefficients)
    
    def get_tuning_status(self) -> str:
        """
        Get human-readable tuning status.
        
        Returns:
            Status string for display
        """
        if self.is_complete():
            return "Tuning complete"
        
        if not self.current_optimizer:
            return "Tuner idle"
        
        coeff_name = self.current_optimizer.coeff_config.name
        iteration = self.current_optimizer.iteration
        step_size = self.current_optimizer.current_step_size
        
        return f"Tuning {coeff_name} (iter {iteration}, step {step_size:.6f})"
