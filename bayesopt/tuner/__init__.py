"""
FRC Shooter Bayesian Tuner

A Driver Station-only Bayesian optimization tuner for the FiringSolutionSolver.
Automatically tunes shooting coefficients based on shot hit/miss feedback.

Usage:
    from tuner import run_tuner
    
    # Run with default config
    run_tuner()
    
    # Or with custom server IP
    run_tuner(server_ip="10.12.34.2")
"""

__version__ = "1.0.0"

from .config import TunerConfig, CoefficientConfig
from .tuner import BayesianTunerCoordinator, run_tuner
from .nt_interface import NetworkTablesInterface, ShotData
from .optimizer import BayesianOptimizer, CoefficientTuner
from .logger import TunerLogger, setup_logging

__all__ = [
    'TunerConfig',
    'CoefficientConfig',
    'BayesianTunerCoordinator',
    'run_tuner',
    'NetworkTablesInterface',
    'ShotData',
    'BayesianOptimizer',
    'CoefficientTuner',
    'TunerLogger',
    'setup_logging',
]
