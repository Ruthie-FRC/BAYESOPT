"""
Configuration constants and default values for the BayesOpt Dashboard.
"""

# Coefficient default values
COEFFICIENT_DEFAULTS = {
    'kDragCoefficient': 0.003,
    'kGravity': 9.81,
    'kShotHeight': 1.0,
    'kTargetHeight': 2.5,
    'kShooterAngle': 45,
    'kShooterRPM': 3000,
    'kExitVelocity': 15
}

# Coefficient configuration with step sizes and ranges
COEFFICIENT_CONFIG = {
    'kDragCoefficient': {'step': 0.0001, 'min': 0.001, 'max': 0.01},
    'kGravity': {'step': 0.01, 'min': 9.0, 'max': 10.0},
    'kShotHeight': {'step': 0.01, 'min': 0.0, 'max': 3.0},
    'kTargetHeight': {'step': 0.01, 'min': 0.0, 'max': 5.0},
    'kShooterAngle': {'step': 1, 'min': 0, 'max': 90},
    'kShooterRPM': {'step': 50, 'min': 0, 'max': 6000},
    'kExitVelocity': {'step': 0.1, 'min': 0, 'max': 30}
}

# Global application state
def get_initial_app_state():
    """Return the initial application state dictionary."""
    return {
        'mode': 'normal',  # 'normal' or 'advanced'
        'theme': 'light',  # 'light' or 'dark'
        'more_features': False,
        'sidebar_collapsed': False,
        'tuner_enabled': False,
        'current_coefficient': 'kDragCoefficient',
        'coefficient_values': {},
        'notes': [],
        'todos': [],
        'selected_algorithm': 'gp',
        'graphs_visible': {
            'success_rate': True,
            'coefficient_history': True,
            'optimization_progress': True,
            'shot_distribution': False
        },
        'banner_dismissed': False,
        'config_locked': False,
        'shot_count': 0,
        'success_rate': 0.0,
        'connection_status': 'disconnected'
    }
