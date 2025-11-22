"""
COEFFICIENT TUNING CONFIGURATION
=================================
This file controls WHAT gets tuned, HOW MUCH it can change, and IN WHAT ORDER.
Edit this file to customize the optimization behavior.

NO CODE CHANGES NEEDED - just modify the values below.
"""

# ============================================================
# TUNING ORDER - What gets optimized and in what sequence
# ============================================================
# The optimizer tunes ONE coefficient at a time in this order.
# Put most impactful coefficients first for fastest improvement.
# Comment out (add # at start) any coefficient you DON'T want to tune.

TUNING_ORDER = [
    "kDragCoefficient",          # Air resistance (MOST IMPACT - tune this first!)
    "kVelocityIterationCount",   # Solver accuracy vs CPU load
    "kAngleIterationCount",      # Solver accuracy vs CPU load
    "kVelocityTolerance",        # How precise velocity calculation needs to be
    "kAngleTolerance",           # How precise angle calculation needs to be
    "kLaunchHeight",             # Physical measurement (tune last - rarely changes)
    # "kAirDensity",             # Commented out - air density is constant (1.225)
]

# ============================================================
# COEFFICIENT DEFINITIONS
# ============================================================
# For each coefficient, you can control:
#   - enabled: True = tune this, False = skip it
#   - default_value: Starting value
#   - min_value: Lowest allowed value (SAFETY LIMIT)
#   - max_value: Highest allowed value (SAFETY LIMIT)
#   - initial_step_size: How big the first changes are
#   - step_decay_rate: How quickly to reduce step size (0.9 = shrink 10% per iteration)
#   - is_integer: True = round to whole numbers, False = allow decimals
#   - nt_key: NetworkTables path (don't change unless robot code changes)

# TODO: Update tuning parameters before testing on robot

COEFFICIENTS = {
    "kDragCoefficient": {
        "enabled": True,               # ← CHANGE THIS to enable/disable tuning
        "default_value": 0.003,        # Starting guess
        "min_value": 0.001,            # ← SAFETY: Can't go below this
        "max_value": 0.006,            # ← SAFETY: Can't go above this
        "initial_step_size": 0.001,    # ← HOW MUCH: Start with big changes
        "step_decay_rate": 0.9,        # Gradually make smaller changes
        "is_integer": False,           # Allow decimals like 0.0035
        "nt_key": "/Tuning/FiringSolver/DragCoefficient",
        "description": "Air resistance coefficient - affects trajectory curvature"
    },
    
    "kAirDensity": {
        "enabled": False,              # ← DISABLED: Air density is constant in FiringSolutionSolver
        "default_value": 1.225,
        "min_value": 1.10,
        "max_value": 1.30,
        "initial_step_size": 0.05,
        "step_decay_rate": 0.9,
        "is_integer": False,
        "nt_key": "/Tuning/FiringSolver/AirDensity",
        "description": "Air density (kg/m³) - typically constant at 1.225"
    },
    
    "kVelocityIterationCount": {
        "enabled": True,               # ← CHANGE THIS to enable/disable tuning
        "default_value": 20,
        "min_value": 10,
        "max_value": 30,               # ← REDUCED from 50 to prevent RoboRIO CPU overload
        "initial_step_size": 5,        # ← HOW MUCH: Try steps of 5 iterations
        "step_decay_rate": 0.85,
        "is_integer": True,            # Must be whole number (10, 11, 12, not 10.5)
        "nt_key": "/Tuning/FiringSolver/VelocityIterations",
        "description": "Solver iterations for velocity - more = accurate but slower"
    },
    
    "kAngleIterationCount": {
        "enabled": True,               # ← CHANGE THIS to enable/disable tuning
        "default_value": 20,
        "min_value": 10,
        "max_value": 30,               # ← REDUCED from 50 to prevent RoboRIO CPU overload
        "initial_step_size": 5,        # ← HOW MUCH: Try steps of 5 iterations
        "step_decay_rate": 0.85,
        "is_integer": True,            # Must be whole number
        "nt_key": "/Tuning/FiringSolver/AngleIterations",
        "description": "Solver iterations for angle - more = accurate but slower"
    },
    
    "kVelocityTolerance": {
        "enabled": True,               # ← CHANGE THIS to enable/disable tuning
        "default_value": 0.01,
        "min_value": 0.005,            # ← SAFETY: Too tight = solver struggles
        "max_value": 0.05,             # ← SAFETY: Too loose = inaccurate
        "initial_step_size": 0.005,    # ← HOW MUCH: Start with 0.005 m/s changes
        "step_decay_rate": 0.9,
        "is_integer": False,
        "nt_key": "/Tuning/FiringSolver/VelocityTolerance",
        "description": "Velocity convergence tolerance (m/s) - smaller = more precise"
    },
    
    "kAngleTolerance": {
        "enabled": True,               # ← CHANGE THIS to enable/disable tuning
        "default_value": 0.0001,
        "min_value": 0.00001,          # ← SAFETY: Too tight = solver struggles
        "max_value": 0.001,            # ← SAFETY: Too loose = inaccurate
        "initial_step_size": 0.0001,   # ← HOW MUCH: Start with 0.0001 rad changes
        "step_decay_rate": 0.9,
        "is_integer": False,
        "nt_key": "/Tuning/FiringSolver/AngleTolerance",
        "description": "Angle convergence tolerance (rad) - smaller = more precise"
    },
    
    "kLaunchHeight": {
        "enabled": True,               # ← CHANGE THIS to enable/disable tuning
        "default_value": 0.8,
        "min_value": 0.75,             # ← SAFETY: Physical robot constraint
        "max_value": 0.85,             # ← SAFETY: Physical robot constraint
        "initial_step_size": 0.02,     # ← HOW MUCH: Start with 2cm changes
        "step_decay_rate": 0.9,
        "is_integer": False,
        "nt_key": "/Tuning/FiringSolver/LaunchHeight",
        "description": "Launch height above ground (m) - physical measurement"
    },
}

# ============================================================
# OPTIMIZATION SETTINGS
# ============================================================
# How the Bayesian optimizer behaves

# How many random points to try before starting intelligent optimization
N_INITIAL_POINTS = 5  # More = better exploration, slower convergence

# Maximum iterations per coefficient before moving to next one
N_CALLS_PER_COEFFICIENT = 20  # More = more thorough, takes longer

# ============================================================
# ROBORIO PROTECTION SETTINGS
# ============================================================
# Prevent overloading the robot's onboard computer

# Maximum coefficient updates per second (prevents NT spam)
MAX_WRITE_RATE_HZ = 5.0  # SAFETY: Don't flood the RoboRIO with updates

# Maximum shot data reads per second (prevents NT spam)
MAX_READ_RATE_HZ = 20.0  # SAFETY: Don't overload NT with read requests

# Batch multiple writes together (reduces NT traffic)
BATCH_WRITES = True  # True = more efficient, False = immediate writes

# ============================================================
# PHYSICAL ROBOT LIMITS (SAFETY)
# ============================================================
# Hardcoded limits based on robot physical capabilities
# Reject any shot data outside these bounds (likely sensor errors)

PHYSICAL_MAX_VELOCITY_MPS = 30.0   # Maximum physically possible exit velocity
PHYSICAL_MIN_VELOCITY_MPS = 5.0    # Minimum physically possible exit velocity
PHYSICAL_MAX_ANGLE_RAD = 1.57      # ~90 degrees (straight up)
PHYSICAL_MIN_ANGLE_RAD = 0.17      # ~10 degrees (very low angle)
PHYSICAL_MAX_DISTANCE_M = 10.0     # Maximum field distance for shots
PHYSICAL_MIN_DISTANCE_M = 1.0      # Minimum shot distance

# ============================================================
# HOW TO USE THIS FILE
# ============================================================
"""
QUICK MODIFICATIONS:

1. DISABLE A COEFFICIENT:
   Set enabled = False in that coefficient's section

2. CHANGE TUNING ORDER:
   Rearrange or comment out items in TUNING_ORDER list

3. ADJUST HOW MUCH IT CHANGES:
   Modify initial_step_size (bigger = more aggressive)

4. TIGHTEN SAFETY LIMITS:
   Reduce the range between min_value and max_value

5. PROTECT ROBORIO:
   Lower MAX_WRITE_RATE_HZ or MAX_READ_RATE_HZ

EXAMPLES:

# Only tune drag coefficient:
TUNING_ORDER = ["kDragCoefficient"]

# Make drag tuning more aggressive:
"initial_step_size": 0.002,  # Change from 0.001

# Tighten drag safety range:
"min_value": 0.002,  # Change from 0.001
"max_value": 0.004,  # Change from 0.006

# Reduce RoboRIO load:
MAX_WRITE_RATE_HZ = 2.0  # Change from 5.0
"""
