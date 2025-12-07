"""
================================================================================
                    COEFFICIENT TUNING CONFIGURATION
================================================================================

This file controls:
  • WHAT coefficients get tuned (enabled = True/False)
  • HOW MUCH they can change (min_value, max_value, step_size)
  • IN WHAT ORDER they are tuned (TUNING_ORDER list)
  • PER-COEFFICIENT OVERRIDES for autotune and auto-advance

For detailed documentation with examples, see:
    docs/AUTOTUNE_GUIDE.md

================================================================================
                       OVERRIDE PRIORITY SYSTEM
================================================================================

Each coefficient can have LOCAL settings that override the global defaults
in TUNER_TOGGLES.ini. Here's how the priority works:

  PRIORITY 1 (HIGHEST): force_global = True in TUNER_TOGGLES.ini
    → ALL coefficients use global settings
    → ALL local overrides are IGNORED
    → Use when you want uniform behavior everywhere

  PRIORITY 2 (MEDIUM): override = True for a coefficient (in THIS file)
    → This coefficient uses its own local settings
    → Other coefficients still use global
    → Only works when force_global = False

  PRIORITY 3 (LOWEST): Global default from TUNER_TOGGLES.ini
    → Used when force_global = False AND override = False
    → This is the fallback for most coefficients

================================================================================
"""

# TODO: Update tuning parameters before testing on robot
# TODO: Measure actual launch height and update kLaunchHeight min/max
# TODO: Verify drag coefficient range is appropriate for your projectile

# ================================================================================
#                              TUNING ORDER
# ================================================================================
# Coefficients are tuned ONE AT A TIME in this order.
#
# TIPS:
#   • Put the most impactful coefficients FIRST
#   • Drag coefficient usually has the biggest effect on accuracy
#   • Physical measurements (launch height) usually need less tuning
#   • Remove a coefficient from this list to skip it entirely
# ================================================================================

TUNING_ORDER = [
    "kDragCoefficient",          # Air resistance - MOST IMPACT, tune first
    "kVelocityIterationCount",   # Solver accuracy vs CPU - affects calculation speed
    "kAngleIterationCount",      # Solver accuracy vs CPU - affects calculation speed
    "kVelocityTolerance",        # Velocity precision - how close is "close enough"
    "kAngleTolerance",           # Angle precision - how close is "close enough"
    "kLaunchHeight",             # Physical measurement - rarely changes
    "kAirDensity",               # Usually constant at 1.225 kg/m³
]


# ================================================================================
#                          COEFFICIENT DEFINITIONS
# ================================================================================
#
# STANDARD SETTINGS (for each coefficient):
#   enabled          : True/False - should this coefficient be tuned?
#   default_value    : Starting value if none exists
#   min_value        : SAFETY LIMIT - optimizer cannot go below this
#   max_value        : SAFETY LIMIT - optimizer cannot go above this
#   initial_step_size: How big are the first changes (gets smaller over time)
#   step_decay_rate  : How fast step size shrinks (0.9 = slow, 0.5 = fast)
#   is_integer       : True if value must be whole number (e.g. iterations)
#   nt_key           : NetworkTables path where this coefficient lives
#   description      : Human-readable explanation
#
# LOCAL OVERRIDES (at bottom of each coefficient):
#   These let you customize autotune/auto-advance for JUST this coefficient.
#   Set the _override flag to True to enable, otherwise global settings apply.
#
#   AUTOTUNE LOCAL SETTINGS:
#     autotune_override       : True = use local settings, False = use global
#     autotune_enabled        : True = auto, False = manual (local setting)
#     autotune_shot_threshold : shots before auto-optimization (local setting)
#
#   AUTO-ADVANCE LOCAL SETTINGS:
#     auto_advance_override       : True = use local, False = use global
#     auto_advance_on_success     : True = auto-skip on 100% hits (local)
#     auto_advance_shot_threshold : shots to check for 100% success (local)
# ================================================================================

COEFFICIENTS = {
    # ----------------------------------------------------------------------------
    # DRAG COEFFICIENT
    # Most impactful parameter - tune this FIRST
    # ----------------------------------------------------------------------------
    # This coefficient represents air resistance on the projectile.
    # Higher values = more drag = shorter, more curved trajectory
    # Lower values = less drag = flatter, longer trajectory
    # ----------------------------------------------------------------------------
    "kDragCoefficient": {
        "enabled": True,               # Include in tuning? True = yes
        "default_value": 0.003,        # Starting value
        "min_value": 0.001,            # SAFETY: Cannot go below this
        "max_value": 0.006,            # SAFETY: Cannot go above this
        "initial_step_size": 0.001,    # Size of first adjustment
        "step_decay_rate": 0.9,        # How fast adjustments shrink
        "is_integer": False,           # Allow decimal values
        "nt_key": "/Tuning/FiringSolver/DragCoefficient",
        "description": "Air resistance coefficient - affects trajectory curvature",
        
        # LOCAL AUTOTUNE OVERRIDE
        # Set autotune_override = True to use these settings instead of global
        "autotune_override": False,        # True = use local, False = use global
        "autotune_enabled": False,         # True = auto, False = manual button
        "autotune_shot_threshold": 10,     # Shots before auto-optimization
        
        # LOCAL AUTO-ADVANCE OVERRIDE
        # Set auto_advance_override = True to use these settings
        "auto_advance_override": False,    # True = use local, False = use global
        "auto_advance_on_success": False,  # True = auto-skip on 100% hits
        "auto_advance_shot_threshold": 10, # Shots to check for 100% success
    },
    
    # ----------------------------------------------------------------------------
    # AIR DENSITY
    # Usually constant at 1.225 kg/m³ - disabled by default
    # ----------------------------------------------------------------------------
    # Air density affects drag force calculation.
    # Standard air density at sea level is 1.225 kg/m³.
    # Only tune this if you're at high altitude or extreme temperatures.
    # ----------------------------------------------------------------------------
    "kAirDensity": {
        "enabled": False,              # DISABLED - rarely needs tuning
        "default_value": 1.225,        # Standard air density at sea level
        "min_value": 1.10,             # SAFETY: Low altitude/hot weather
        "max_value": 1.30,             # SAFETY: High altitude/cold weather
        "initial_step_size": 0.05,
        "step_decay_rate": 0.9,
        "is_integer": False,
        "nt_key": "/Tuning/FiringSolver/AirDensity",
        "description": "Air density (kg/m³) - typically constant at 1.225",
        
        # Local autotune override
        "autotune_override": False,
        "autotune_enabled": False,
        "autotune_shot_threshold": 10,
        # Local auto-advance override
        "auto_advance_override": False,
        "auto_advance_on_success": False,
        "auto_advance_shot_threshold": 10,
    },
    
    # ----------------------------------------------------------------------------
    # VELOCITY ITERATION COUNT
    # Solver accuracy vs CPU usage tradeoff
    # ----------------------------------------------------------------------------
    # Controls how many iterations the solver runs to find velocity.
    # More iterations = more accurate but slower calculations
    # Fewer iterations = faster but potentially less accurate
    # ----------------------------------------------------------------------------
    "kVelocityIterationCount": {
        "enabled": True,
        "default_value": 20,           # 20 iterations is usually good
        "min_value": 10,               # SAFETY: Minimum for acceptable accuracy
        "max_value": 30,               # SAFETY: Maximum before CPU impact
        "initial_step_size": 5,        # Adjust by 5 iterations at a time
        "step_decay_rate": 0.85,
        "is_integer": True,            # Must be whole number
        "nt_key": "/Tuning/FiringSolver/VelocityIterations",
        "description": "Solver iterations for velocity - more = accurate but slower",
        
        # Local autotune override
        "autotune_override": False,
        "autotune_enabled": False,
        "autotune_shot_threshold": 10,
        # Local auto-advance override
        "auto_advance_override": False,
        "auto_advance_on_success": False,
        "auto_advance_shot_threshold": 10,
    },
    
    # ----------------------------------------------------------------------------
    # ANGLE ITERATION COUNT
    # Solver accuracy vs CPU usage tradeoff
    # ----------------------------------------------------------------------------
    # Controls how many iterations the solver runs to find angle.
    # More iterations = more accurate but slower calculations
    # Fewer iterations = faster but potentially less accurate
    # ----------------------------------------------------------------------------
    "kAngleIterationCount": {
        "enabled": True,
        "default_value": 20,           # 20 iterations is usually good
        "min_value": 10,               # SAFETY: Minimum for acceptable accuracy
        "max_value": 30,               # SAFETY: Maximum before CPU impact
        "initial_step_size": 5,        # Adjust by 5 iterations at a time
        "step_decay_rate": 0.85,
        "is_integer": True,            # Must be whole number
        "nt_key": "/Tuning/FiringSolver/AngleIterations",
        "description": "Solver iterations for angle - more = accurate but slower",
        
        # Local autotune override
        "autotune_override": False,
        "autotune_enabled": False,
        "autotune_shot_threshold": 10,
        # Local auto-advance override
        "auto_advance_override": False,
        "auto_advance_on_success": False,
        "auto_advance_shot_threshold": 10,
    },
    
    # ----------------------------------------------------------------------------
    # VELOCITY TOLERANCE
    # Convergence precision - how close is "close enough"?
    # ----------------------------------------------------------------------------
    # When the solver calculates velocity, this is how close to the target
    # velocity it needs to get before declaring "good enough".
    # Smaller values = more precise but may take more iterations
    # Larger values = faster convergence but less precise
    # ----------------------------------------------------------------------------
    "kVelocityTolerance": {
        "enabled": True,
        "default_value": 0.01,         # 0.01 m/s tolerance
        "min_value": 0.005,            # SAFETY: Very precise
        "max_value": 0.05,             # SAFETY: Less precise
        "initial_step_size": 0.005,
        "step_decay_rate": 0.9,
        "is_integer": False,
        "nt_key": "/Tuning/FiringSolver/VelocityTolerance",
        "description": "Velocity convergence tolerance (m/s) - smaller = more precise",
        
        # Local autotune override
        "autotune_override": False,
        "autotune_enabled": False,
        "autotune_shot_threshold": 10,
        # Local auto-advance override
        "auto_advance_override": False,
        "auto_advance_on_success": False,
        "auto_advance_shot_threshold": 10,
    },
    
    # ----------------------------------------------------------------------------
    # ANGLE TOLERANCE
    # Convergence precision - how close is "close enough"?
    # ----------------------------------------------------------------------------
    # When the solver calculates angle, this is how close to the target
    # angle it needs to get before declaring "good enough".
    # Smaller values = more precise but may take more iterations
    # Larger values = faster convergence but less precise
    # ----------------------------------------------------------------------------
    "kAngleTolerance": {
        "enabled": True,
        "default_value": 0.0001,       # 0.0001 radians tolerance
        "min_value": 0.00001,          # SAFETY: Very precise
        "max_value": 0.001,            # SAFETY: Less precise
        "initial_step_size": 0.0001,
        "step_decay_rate": 0.9,
        "is_integer": False,
        "nt_key": "/Tuning/FiringSolver/AngleTolerance",
        "description": "Angle convergence tolerance (rad) - smaller = more precise",
        
        # Local autotune override
        "autotune_override": False,
        "autotune_enabled": False,
        "autotune_shot_threshold": 10,
        # Local auto-advance override
        "auto_advance_override": False,
        "auto_advance_on_success": False,
        "auto_advance_shot_threshold": 10,
    },
    
    # ----------------------------------------------------------------------------
    # LAUNCH HEIGHT
    # Physical measurement - measure this on your robot!
    # ----------------------------------------------------------------------------
    # Height of the projectile launch point above the ground.
    # This is a physical measurement that should be accurate from the start.
    # Minor tuning may help compensate for measurement errors.
    # ----------------------------------------------------------------------------
    "kLaunchHeight": {
        "enabled": True,
        "default_value": 0.8,          # 0.8 meters (about 31 inches)
        "min_value": 0.75,             # SAFETY: Measure your robot's actual range
        "max_value": 0.85,             # SAFETY: Measure your robot's actual range
        "initial_step_size": 0.02,     # Small adjustments for physical parameter
        "step_decay_rate": 0.9,
        "is_integer": False,
        "nt_key": "/Tuning/FiringSolver/LaunchHeight",
        "description": "Launch height above ground (m) - physical measurement",
        
        # Local autotune override
        "autotune_override": False,
        "autotune_enabled": False,
        "autotune_shot_threshold": 10,
        # Local auto-advance override
        "auto_advance_override": False,
        "auto_advance_on_success": False,
        "auto_advance_shot_threshold": 10,
    },
}

# ================================================================================
#                          OPTIMIZATION SETTINGS
# ================================================================================
# Controls how the Bayesian optimization algorithm behaves.
# ================================================================================

# How many random samples before the optimizer starts being "smart"
# More initial points = better exploration but slower to start optimizing
N_INITIAL_POINTS = 5

# Maximum iterations per coefficient before moving to the next
# After this many attempts, the optimizer gives up and moves on
N_CALLS_PER_COEFFICIENT = 20


# ================================================================================
#                         ROBORIO PROTECTION
# ================================================================================
# Rate limits to prevent overloading the RoboRIO with too many NT updates.
# ================================================================================

MAX_WRITE_RATE_HZ = 5.0    # Max coefficient updates per second
MAX_READ_RATE_HZ = 20.0    # Max shot data reads per second
BATCH_WRITES = True        # Batch multiple writes together for efficiency


# ================================================================================
#                          PHYSICAL LIMITS (SAFETY)
# ================================================================================
# Hard limits to reject obviously invalid shot data.
# These should match your robot's actual physical capabilities.
# ================================================================================

PHYSICAL_MAX_VELOCITY_MPS = 30.0   # Maximum possible launch velocity (m/s)
PHYSICAL_MIN_VELOCITY_MPS = 5.0    # Minimum realistic launch velocity (m/s)
PHYSICAL_MAX_ANGLE_RAD = 1.57      # Maximum launch angle (~90 degrees)
PHYSICAL_MIN_ANGLE_RAD = 0.17      # Minimum launch angle (~10 degrees)
PHYSICAL_MAX_DISTANCE_M = 10.0     # Maximum target distance (m)
PHYSICAL_MIN_DISTANCE_M = 1.0      # Minimum target distance (m)
