# Developer Guide

Comprehensive guide for developers and maintainers of the BayesOpt tuner.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Code Organization](#code-organization)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Making Changes](#making-changes)
- [Contributing](#contributing)
- [Adapting for Non-FRC Use](#adapting-for-non-frc-use)

## Overview

### Purpose

This document is for developers, maintainers, and advanced users who want to understand or modify the system internals.

**For operational documentation, see [USER_GUIDE.md](USER_GUIDE.md).**

### What This System Does

The BayesOpt tuner uses Bayesian optimization to automatically tune coefficients for a robot shooting system. It:
- Runs on a host machine (Driver Station laptop)
- Reads performance telemetry via NetworkTables
- Uses Bayesian optimization to propose coefficient updates
- Tunes one coefficient at a time in a configured order
- Implements safety features (clamping, rate-limits, match-mode disable)

### Bayesian Optimization Primer

Bayesian optimization is a sample-efficient method for tuning expensive or noisy black-box functions:
- Builds a probabilistic surrogate model (commonly a Gaussian Process)
- Uses an acquisition function to select promising points
- Balances exploration vs exploitation
- Efficient for scenarios with limited samples

In this system:
- Robot performance (shot accuracy) is the objective
- Optimizer proposes coefficient changes
- Receives shot scores as feedback
- Updates surrogate to suggest improved coefficients

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│  HOST MACHINE (Driver Station Laptop)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Launcher (START_TUNER.bat/sh)                            │  │
│  │  ├─ tuner_daemon.py                                       │  │
│  └──┴──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Coordinator (tuner/tuner.py)                             │  │
│  │  ├─ Main loop and orchestration                           │  │
│  │  ├─ Safety checks (match mode, invalid data)             │  │
│  │  ├─ Rate limiting and clamping                            │  │
│  │  ├─ Coefficient sequencing                                │  │
│  └──┬──────────────────────────────────────────────────────────┘  │
│     │                                                            │
│     ├──► NetworkTables Interface (tuner/nt_interface.py)       │
│     │    ├─ Connection management                               │
│     │    ├─ Read shot data                                      │
│     │    └─ Write coefficients                                  │
│     │                                                            │
│     ├──► Optimizer (tuner/optimizer.py)                         │
│     │    ├─ Bayesian optimization                               │
│     │    ├─ Gaussian Process surrogate                          │
│     │    └─ Acquisition function                                │
│     │                                                            │
│     ├──► Logger (tuner/logger.py)                               │
│     │    ├─ CSV logging                                         │
│     │    └─ Event logging                                       │
│     │                                                            │
│     └──► Config (tuner/config.py)                               │
│          ├─ Load TUNER_TOGGLES.ini                              │
│          └─ Load COEFFICIENT_TUNING.py                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ NetworkTables
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ROBOT (RoboRIO)                                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Java Robot Code (FiringSolver.java)                      │  │
│  │  ├─ Publishes shot data                                   │  │
│  │  ├─ Reads coefficient updates                             │  │
│  │  └─ Uses coefficients in calculations                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

**Step-by-step:**

1. **Launcher** starts daemon → constructs TunerConfig → starts Coordinator
2. **Coordinator** loop polls `nt_interface.read_shot_data()` at configured rate
3. **Shot data** is validated (physically plausible values)
4. **Valid samples** sent to active CoefficientTuner (optimizer)
5. **Optimizer** suggests next value using Gaussian Process model
6. **Coordinator** clamps suggestion to bounds, enforces rate limits
7. **Coordinator** calls `nt_interface.write_coefficient(name, value)`
8. **Shot outcomes** reported to optimizer via `report_result(value, score)`
9. **Logger** records inputs, suggestions, results, state changes

### State Machine

```
[IDLE]
  │
  ├─ start() ────────────────────► [TUNING_LOOP]
                                         │
                                         ├─ match_mode ──► [DISABLED]
                                         │                      │
                                         │                      └─ match_end ──► [TUNING_LOOP]
                                         │
                                         ├─ invalid_data ─► [PAUSED]
                                         │                      │
                                         │                      └─ good_data ──► [TUNING_LOOP]
                                         │
                                         ├─ converged ─────► [NEXT_COEFFICIENT or COMPLETE]
                                         │
                                         └─ stop() ────────► [SHUTDOWN]
```

## Project Structure

### Directory Layout

```
BAYESOPT/
├── README.md                          # Main overview and quick start
├── LICENSE                            # License file
├── START_TUNER.bat                    # Windows launcher
├── START_TUNER.sh                     # Mac/Linux launcher
├── CREATE_DESKTOP_SHORTCUT.bat        # Windows shortcut creator
│
├── docs/                              # User documentation
│   ├── SETUP.md                       # Setup instructions
│   ├── USER_GUIDE.md                  # Complete user guide
│   ├── JAVA_INTEGRATION.md            # Robot code integration
│   ├── TROUBLESHOOTING.md             # Problem solving
│   ├── DEVELOPER_GUIDE.md             # This file
│   └── CONTRIBUTING.md                # Contribution guidelines
│
├── bayesopt/                          # Main Python package
│   ├── config/                        # Configuration files
│   │   ├── TUNER_TOGGLES.ini          # Global settings
│   │   └── COEFFICIENT_TUNING.py      # Coefficient definitions
│   │
│   ├── tuner/                         # Core tuner code
│   │   ├── main.py                    # Entry point
│   │   ├── tuner.py                   # Coordinator/orchestrator
│   │   ├── optimizer.py               # Bayesian optimization
│   │   ├── nt_interface.py            # NetworkTables interface
│   │   ├── config.py                  # Config loader/validator
│   │   ├── logger.py                  # Logging
│   │   ├── gui.py                     # GUI window
│   │   ├── requirements.txt           # Python dependencies
│   │   ├── run_tests.py               # Test runner
│   │   └── tests/                     # Unit tests
│   │       ├── test_optimizer.py
│   │       ├── test_config.py
│   │       └── test_tuner.py
│   │
│   ├── scripts/                       # Utility scripts
│   └── docs/                          # (Legacy, being removed)
│
├── java-integration/                  # Java robot code
│   ├── README.md                      # Java integration guide
│   ├── FiringSolver.java              # Example subsystem
│   ├── TunerInterface.java            # Helper class
│   ├── TunableNumber.java             # Simple tunable number
│   ├── LoggedTunableNumber.java       # AdvantageKit version
│   └── Constants_Addition.java        # Constants to add
│
└── tuner_logs/                        # Generated logs (not in git)
    ├── bayesian_tuner_*.csv           # Shot data
    ├── coefficient_history_*.json     # Coefficient changes
    └── coefficient_interactions_*.json # Detected interactions
```

## How It Works

### Main Loop (tuner.py)

```python
while running:
    # 1. Read shot data from NetworkTables
    shot_data = nt_interface.read_shot_data()
    
    # 2. Validate data
    if not validate(shot_data):
        handle_invalid_data()
        continue
    
    # 3. Check safety conditions
    if nt_interface.is_match_mode():
        pause_tuning()
        continue
    
    # 4. Feed to optimizer
    current_tuner.add_shot(shot_data)
    
    # 5. Check if should optimize
    if should_optimize():
        suggestion = current_tuner.suggest_next_value()
        clamped = clamp(suggestion, min, max)
        
        # 6. Rate limiting
        if can_write(coefficient_name):
            nt_interface.write_coefficient(name, clamped)
            log_event(name, clamped)
    
    # 7. Check advancement
    if should_advance():
        advance_to_next_coefficient()
```

### Optimizer (optimizer.py)

**BayesianOptimizer class:**

```python
class BayesianOptimizer:
    def __init__(self, bounds, n_initial_points=5):
        self.optimizer = skopt.Optimizer(
            dimensions=bounds,
            n_initial_points=n_initial_points,
            acq_func='EI'  # Expected Improvement
        )
    
    def suggest_next_value(self):
        # Ask optimizer for next point to try
        return self.optimizer.ask()
    
    def report_result(self, value, score):
        # Tell optimizer the result
        self.optimizer.tell(value, -score)  # Negative for maximization
```

**Per-coefficient tuner:**

```python
class CoefficientTuner:
    def __init__(self, coefficient_config):
        bounds = [(config.min, config.max)]
        self.optimizer = BayesianOptimizer(bounds)
        self.shots = []
    
    def add_shot(self, shot_data):
        self.shots.append(shot_data)
    
    def optimize(self):
        suggestion = self.optimizer.suggest_next_value()
        return suggestion
    
    def report_result(self, value, score):
        self.optimizer.report_result(value, score)
```

### NetworkTables Interface (nt_interface.py)

**Key methods:**

```python
class NetworkTablesInterface:
    def start(self, server_address):
        NetworkTables.initialize(server=server_address)
        # Wait for connection...
    
    def read_shot_data(self):
        # Read from /FiringSolver/ table
        timestamp = table.getNumber("ShotTimestamp", 0)
        if timestamp == self.last_timestamp:
            return None  # No new shot
        
        return ShotData(
            hit=table.getBoolean("Hit"),
            distance=table.getNumber("Distance"),
            pitch=solution_table.getNumber("pitchRadians"),
            velocity=solution_table.getNumber("exitVelocity"),
            # ... etc
        )
    
    def write_coefficient(self, name, value):
        # Write to /Tuning/Coefficients/ table
        coeff_table.putNumber(name, value)
    
    def is_match_mode(self):
        # Check for FMS connection
        return fms_attached
```

## Code Organization

### Where Logic Lives

| File | Responsibility | When to modify |
|------|---------------|----------------|
| **bayesopt/config/COEFFICIENT_TUNING.py** | Coefficient definitions, bounds, tuning order | Add/modify coefficients, change ranges |
| **bayesopt/config/TUNER_TOGGLES.ini** | Global settings, toggles | Add runtime flags |
| **bayesopt/tuner/config.py** | Load and validate config | Add config validation |
| **bayesopt/tuner/tuner.py** | Orchestration, safety checks, sequencing | Change tuning logic, add safety features |
| **bayesopt/tuner/optimizer.py** | Bayesian optimization algorithm | Change optimization algorithm |
| **bayesopt/tuner/nt_interface.py** | NetworkTables communication | Change telemetry source, add NT keys |
| **bayesopt/tuner/logger.py** | Logging and CSV output | Add log fields, change format |
| **bayesopt/tuner/gui.py** | GUI window | Change UI appearance |
| **bayesopt/tuner/tests/** | Unit tests | Add test coverage |

### Interaction Matrix

```
tuner_daemon.py
    └─► tuner.Tuner (start/stop)

tuner.Tuner
    ├─► nt_interface (read/write)
    ├─► optimizer (suggest/report)
    ├─► logger (log events)
    └─► config (load settings)

optimizer
    └─► logger (debug events)

nt_interface
    └─► logger (connection events)

tests
    └─► mock nt_interface
```

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- Text editor or IDE (VSCode recommended)

### Clone and Setup

```bash
# Clone repository
git clone https://github.com/Ruthie-FRC/BAYESOPT.git
cd BAYESOPT

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r bayesopt/tuner/requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8
```

### Running Tests

```bash
# Run all tests
cd bayesopt/tuner
python run_tests.py

# Run specific test file
python -m pytest tests/test_optimizer.py

# Run with coverage
python -m pytest --cov=. tests/
```

### Code Style

The project follows PEP 8 style guidelines.

```bash
# Format code
black bayesopt/tuner/

# Check style
flake8 bayesopt/tuner/

# Type hints (if using mypy)
mypy bayesopt/tuner/
```

## Testing

### Testing Strategy

**Unit tests must:**
- Run offline (no robot required)
- Mock NetworkTables interface
- Validate core logic independently

**Test categories:**

1. **Config tests** - Validate configuration loading and validation
2. **Optimizer tests** - Test Bayesian optimization logic
3. **Coordinator tests** - Test orchestration, safety, sequencing
4. **Integration tests** - Test component interactions

### Mocking NetworkTables

```python
# tests/test_tuner.py
class MockNTInterface:
    def __init__(self):
        self.shots = []
        self.coefficients = {}
    
    def read_shot_data(self):
        if self.shots:
            return self.shots.pop(0)
        return None
    
    def write_coefficient(self, name, value):
        self.coefficients[name] = value

# Use in tests
def test_optimization():
    mock_nt = MockNTInterface()
    tuner = Tuner(mock_nt)
    
    # Feed synthetic shot data
    mock_nt.shots = [
        ShotData(hit=True, distance=3.0, ...),
        ShotData(hit=False, distance=4.0, ...),
    ]
    
    # Run tuner logic
    tuner.step()
    
    # Assert expected behavior
    assert 'kDragCoefficient' in mock_nt.coefficients
```

### Running Tests

```bash
# All tests
python run_tests.py

# Specific test
python -m pytest tests/test_optimizer.py::test_suggest_value

# With verbose output
python -m pytest -v

# With coverage
python -m pytest --cov=bayesopt.tuner --cov-report=html
```

## Making Changes

### Common Modification Scenarios

#### Add a New Coefficient

**1. Define in COEFFICIENT_TUNING.py:**
```python
"kNewCoefficient": {
    "min": 0.0,
    "max": 10.0,
    "default": 5.0,
    "nt_path": "/Tuning/Coefficients",
    "nt_key": "kNewCoefficient",
}

# Add to TUNING_ORDER
TUNING_ORDER = [
    "kDragCoefficient",
    "kNewCoefficient",  # Added
    # ...
]
```

**2. Update robot code to read coefficient**

**3. Add tests:**
```python
def test_new_coefficient_clamping():
    config = load_config()
    assert config.coefficients["kNewCoefficient"].min == 0.0
    # ...
```

#### Change Optimization Algorithm

**Modify optimizer.py while keeping API:**

```python
class BayesianOptimizer:
    def suggest_next_value(self):
        # New algorithm here
        return suggestion
    
    def report_result(self, value, score):
        # Update surrogate
        pass
    
    def is_converged(self):
        # Convergence check
        return False
```

**Update tests to validate new behavior**

#### Add Runtime Toggle

**1. Add to TUNER_TOGGLES.ini:**
```ini
[main_controls]
new_feature_enabled = True
```

**2. Add to config.py:**
```python
@dataclass
class TunerConfig:
    # ...
    new_feature_enabled: bool = False
```

**3. Update loader:**
```python
def load_config():
    config.new_feature_enabled = ini.getboolean(
        'main_controls',
        'new_feature_enabled',
        fallback=False
    )
```

**4. Use in tuner.py:**
```python
if self.config.new_feature_enabled:
    # Feature logic
    pass
```

#### Change Logging Fields

**1. Update logger.py CSV header:**
```python
def _initialize_csv_log(self):
    headers = [
        'timestamp',
        'coefficient_name',
        'new_field',  # Added
        # ...
    ]
```

**2. Update log_shot method:**
```python
def log_shot(self, shot_data):
    row = [
        timestamp,
        coeff_name,
        new_field_value,  # Added
        # ...
    ]
```

**3. Update tests to validate columns**

#### Integrate Different Data Source

**Replace nt_interface.py while keeping API:**

```python
class MyCustomInterface:
    def start(self, address):
        # Your connection logic
        pass
    
    def read_shot_data(self):
        # Read from your source
        return ShotData(...)
    
    def write_coefficient(self, name, value):
        # Write to your destination
        pass
    
    def is_match_mode(self):
        # Your safety check
        return False
```

**Use in tuner.py:**
```python
# Instead of NetworkTablesInterface
interface = MyCustomInterface()
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code style guidelines
- Commit message format
- Pull request process
- Issue reporting

**Quick guidelines:**
- Write tests for new features
- Follow existing code style
- Document public APIs
- Keep changes focused and small
- Explain why, not just what

## Adapting for Non-FRC Use

### For Academic/Research Use

The system can be adapted for other optimization tasks:

**1. Define your coefficients** in COEFFICIENT_TUNING.py
**2. Implement data interface** (replace NetworkTables)
**3. Define performance metric** (replace hit/miss)
**4. Configure bounds and convergence criteria**

**Example applications:**
- Control system tuning (PID, LQR)
- Machine learning hyperparameters
- Manufacturing process optimization
- Robotics motion planning
- Any black-box optimization problem

### Contact for Academic Use

If you're an educator or researcher interested in adapting this for your work:
- Open GitHub issue describing your use case
- Contact maintainers for guidance
- We're happy to help configure for your needs

### Open Source Notes

- **License:** See LICENSE file
- **Attribution:** Please credit original authors if using/adapting
- **No compensation expected:** Free to use
- **Contributions welcome:** Open source project

## Debugging Checklist

**Connection issues:**
- Is NT connected? Check logs
- Can ping robot?
- Firewall blocking?

**Tuner not running:**
- Match mode? Check `is_match_mode()`
- Invalid data? Check validation logs
- Enabled? Check `TunerEnabled`

**Optimization issues:**
- Enough shots? Check threshold
- Valid ranges? Check bounds
- Rate limited? Check timestamps

**Performance issues:**
- Reduce iterations
- Check CPU usage
- Review log retention

## See Also

### Project Documentation
- **User Guide:** [USER_GUIDE.md](USER_GUIDE.md) - Complete user documentation
- **Setup:** [SETUP.md](SETUP.md) - Installation instructions
- **Java Integration:** [JAVA_INTEGRATION.md](JAVA_INTEGRATION.md) - Robot code integration
- **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- **Documentation Standards:** [DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) - Documentation conventions

### External Resources
- **Scikit-optimize docs:** [scikit-optimize.github.io](https://scikit-optimize.github.io/)
- **NetworkTables:** [robotpy.readthedocs.io](https://robotpy.readthedocs.io/)
