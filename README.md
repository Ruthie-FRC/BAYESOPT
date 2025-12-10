# BAYESOPT - Bayesian Optimization Tuner for FRC Robots

A comprehensive tuning system using Bayesian optimization to automatically tune shooting coefficients on FRC robots.

## 📖 Table of Contents

- [Overview](#overview)
- [Quick Setup](#quick-setup)
- [How to Run](#how-to-run)
- [Documentation](#documentation)
- [Key Features](#key-features)
- [Requirements](#requirements)

## Overview

**What is this?** A Python application that runs on your Driver Station laptop and automatically tunes your robot's shooting coefficients using Bayesian optimization.

**How it works:**
```
Driver Station Laptop          Network          Robot
┌─────────────────────┐        ┌─────┐         ┌─────────────────────┐
│  Python Tuner App   │◄──────►│ NT  │◄───────►│  Java Robot Code    │
│  (double-click .bat)│        └─────┘         │  (on RoboRIO)       │
│                     │                        │                     │
│  • Runs optimization│                        │  • Publishes shots  │
│  • Shows GUI        │                        │  • Reads coefficients│
│  • Writes coeffs    │                        │  • Uses in FiringSolver
└─────────────────────┘                        └─────────────────────┘
```

**The tuner communicates with your robot through NetworkTables:**
1. Robot publishes shot data (hit/miss, distance, velocity, etc.)
2. Python tuner reads the data and runs optimization
3. Tuner writes updated coefficients to NetworkTables
4. Robot reads and uses the new coefficients

## Quick Setup

### First-Time Setup (Do This Once)

1. **Install Python** (3.8 or newer) - [Download here](https://www.python.org/downloads/)
   - ⚠️ Make sure to check "Add Python to PATH" during installation

2. **Install dependencies:**
   ```bash
   pip install -r bayesopt/tuner/requirements.txt
   ```

3. **Create Desktop shortcut:**
   - **Windows:** Double-click `CREATE_DESKTOP_SHORTCUT.bat`
   - **Mac/Linux:** Run `./START_TUNER.sh` (first run `chmod +x START_TUNER.sh`)
   
   A "BayesOpt Tuner" shortcut will appear on your Desktop!

4. **Set up Java robot code:**
   - See [JAVA_INTEGRATION.md](bayesopt/docs/JAVA_INTEGRATION.md) for complete integration guide
   - Copy files from `java-integration/` folder into your robot project

### Verify Installation

Run the unit tests to make sure everything works:
```bash
cd bayesopt/tuner
python run_tests.py
```
All tests should pass ✅

## How to Run

### Starting the Tuner

**Option 1 (Recommended):** Double-click the "BayesOpt Tuner" Desktop shortcut

**Option 2:** Run manually:
- **Windows:** Double-click `START_TUNER.bat`
- **Mac/Linux:** Run `./START_TUNER.sh`

### Using the Tuner

Once running, the GUI window shows:
- ✅ Connection status to robot
- 📊 Current coefficient being tuned
- 🎯 Shot count and progress
- 📝 Real-time log messages

**Control the tuner from the dashboard** at `/Tuning/BayesianTuner/`:
- Toggle `TunerEnabled` to turn on/off
- Press `RunOptimization` to optimize (in manual mode)
- Press `SkipToNextCoefficient` to advance (in manual mode)
- Use `ManualControl/` to adjust coefficients manually

**Or use keyboard hotkeys** (see [HOTKEYS.md](bayesopt/docs/HOTKEYS.md)):
- `Ctrl+Shift+X` - Stop tuner
- `Ctrl+Shift+R` - Run optimization
- `Ctrl+Shift+Right` - Next coefficient
- `Ctrl+Shift+Left` - Previous coefficient

### Configuration

Edit these files to customize behavior:

| File | What it controls |
|------|------------------|
| `bayesopt/config/TUNER_TOGGLES.ini` | Global settings (autotune, thresholds) |
| `bayesopt/config/COEFFICIENT_TUNING.py` | Coefficient ranges, tuning order |

**Manual Mode (default, recommended for first use):**
```ini
autotune_enabled = False              # You press button to optimize
auto_advance_on_success = False       # You press button to advance
```

**Automatic Mode (hands-free tuning):**
```ini
autotune_enabled = True               # Auto-optimize every N shots
autotune_shot_threshold = 10
auto_advance_on_success = True        # Auto-advance on 100% success
auto_advance_shot_threshold = 10
```

## Documentation

### 📚 Complete Guides

| Document | When to use it |
|----------|----------------|
| **[SETUP.md](bayesopt/docs/SETUP.md)** | Detailed setup instructions for all platforms |
| **[USER_GUIDE.md](bayesopt/docs/USER_GUIDE.md)** | Complete feature guide, dashboard controls, configuration |
| **[HOTKEYS.md](bayesopt/docs/HOTKEYS.md)** | Keyboard shortcuts reference and troubleshooting |
| **[JAVA_INTEGRATION.md](bayesopt/docs/JAVA_INTEGRATION.md)** | **REQUIRED:** How to integrate with your robot code |
| **[TROUBLESHOOTING.md](bayesopt/docs/TROUBLESHOOTING.md)** | Common problems and solutions |
| **[DEVELOPER_GUIDE.md](bayesopt/docs/DEVELOPER_GUIDE.md)** | Architecture, code structure, development info |

### 📂 Quick References

- **Java integration files:** See `java-integration/` folder
- **Configuration examples:** See `bayesopt/config/` folder
- **Contributing:** See [CONTRIBUTING.md](bayesopt/docs/CONTRIBUTING.md)

## Key Features

### Intelligent Optimization
- **Bayesian optimization** for efficient coefficient tuning
- **Per-coefficient tuning** with configurable order
- **Automatic convergence detection** to know when tuning is complete

### Flexible Control Modes
- **Manual mode:** You control when to optimize and advance
- **Automatic mode:** Runs optimization and advances automatically
- **Mixed mode:** Auto-optimize but manual advance (or vice versa)

### Real-Time Controls
- **Enable/disable** tuner without restarting
- **Manual coefficient adjustment** from dashboard
- **Fine-tuning mode** for aim bias (LEFT, RIGHT, UP, DOWN)
- **Backtrack** to re-tune earlier coefficients

### Comprehensive Logging
- Shot-by-shot CSV logs with all coefficients
- Coefficient history JSON with timestamps
- Interaction detection for dependent coefficients

### Safety Features
- Automatic coefficient clamping to safe ranges
- Match-mode auto-disable (no tuning during matches)
- Invalid data detection and handling
- Rate-limiting for coefficient updates

## Requirements

- **Python 3.8+** on Driver Station laptop
- **NetworkTables connection** to robot
- **Java robot code** integrated with NetworkTables (see JAVA_INTEGRATION.md)

**Python dependencies:**
```bash
pip install -r bayesopt/tuner/requirements.txt
```

## License

See [LICENSE](LICENSE) file for details.
