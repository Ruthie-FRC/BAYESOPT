# User Guide

Complete guide to using the BayesOpt tuner system.

## Table of Contents

- [Getting Started](#getting-started)
- [Basic Operation](#basic-operation)
- [Configuration](#configuration)
- [Keyboard Hotkeys](#keyboard-hotkeys)
- [Dashboard Controls](#dashboard-controls)
- [Features](#features)
- [Usage Modes](#usage-modes)
- [Advanced Features](#advanced-features)
- [Logging and Data](#logging-and-data)

## Getting Started

### First-Time Users

If you're using the tuner for the first time, start with **Manual Mode**:

1. **Edit `bayesopt/config/TUNER_TOGGLES.ini`:**
   ```ini
   autotune_enabled = False              # Manual optimization
   auto_advance_on_success = False       # Manual advancement
   ```

2. **Start the tuner:**
   - Double-click the "BayesOpt Tuner" Desktop shortcut
   - Or run `START_TUNER.bat` (Windows) / `START_TUNER.sh` (Mac/Linux)

3. **Connect to robot:**
   - GUI shows connection status
   - Should display "Connected" in green when ready

4. **Enable tuning:**
   - On dashboard, set `/Tuning/BayesianTuner/TunerEnabled` to `True`

### Quick Start Workflow

1. **Enable tuner** via dashboard toggle
2. **Take shots** - Robot logs data automatically
3. **Press "Run Optimization"** button when ready
4. **Review results** - Check shot accuracy
5. **Press "Skip to Next Coefficient"** when satisfied
6. **Repeat** for each coefficient

## Basic Operation

### The GUI Window

When running, the GUI shows:

| Element | Shows |
|---------|-------|
| **Connection Status** | Green "Connected" or Red "Disconnected" |
| **Current Coefficient** | Which coefficient is being tuned |
| **Shot Count** | Number of shots accumulated |
| **Progress Bar** | Visual progress toward threshold |
| **Log Output** | Real-time messages and events |

### The Tuning Process

The tuner works through coefficients in a configured order:

1. **Accumulate shots** for current coefficient
2. **Run optimization** (manual or automatic)
3. **Update coefficient** based on results
4. **Repeat** until convergence or manual advance
5. **Move to next coefficient** (manual or automatic)

### Manual vs Automatic Control

**Manual Mode (Recommended for beginners):**
- You control when to optimize (press button)
- You control when to advance (press button)
- Full visibility and control over the process

**Automatic Mode (For experienced users):**
- Optimization runs automatically every N shots
- Advancement happens automatically on 100% success
- Hands-free operation for long tuning sessions

## Configuration

### Main Configuration Files

#### TUNER_TOGGLES.ini

Global settings that apply to all coefficients (unless overridden).

**Location:** `bayesopt/config/TUNER_TOGGLES.ini`

**Key settings:**
```ini
[main_controls]

# === AUTOTUNE (when optimization runs) ===
autotune_enabled = False           # True = auto, False = manual button
autotune_shot_threshold = 10       # Shots before auto-optimization
autotune_force_global = False      # True = ignore local overrides

# === AUTO-ADVANCE (when to move to next coefficient) ===
auto_advance_on_success = False    # True = advance on 100% hits
auto_advance_shot_threshold = 10   # Shots to check for success
auto_advance_force_global = False  # True = ignore local overrides
```

#### COEFFICIENT_TUNING.py

Per-coefficient settings and tuning order.

**Location:** `bayesopt/config/COEFFICIENT_TUNING.py`

**Defines:**
- Coefficient ranges (min/max values)
- Initial default values
- Tuning order
- Per-coefficient overrides (optional)

**Example:**
```python
"kDragCoefficient": {
    "min": 0.3,
    "max": 0.7,
    "default": 0.47,
    "autotune_override": False,        # Use global settings
    "auto_advance_override": False,    # Use global settings
}
```

### Configuration Priority System

The system uses a 3-level priority:

```
1. FORCE GLOBAL (highest)
   If force_global = True → ALL coefficients use global settings
   
2. LOCAL OVERRIDE (medium)
   If override = True → This coefficient uses its own settings
   
3. GLOBAL DEFAULT (lowest)
   Falls back to TUNER_TOGGLES.ini values
```

**Decision flow:**
```
Is force_global = True?
    YES → Use GLOBAL settings
    NO → Is local override = True?
            YES → Use LOCAL settings
            NO → Use GLOBAL settings
```

## Keyboard Hotkeys

The tuner provides keyboard shortcuts for quick access to common functions. See [HOTKEYS.md](HOTKEYS.md) for complete documentation.

### Quick Reference

| Hotkey | Function | Fallback |
|--------|----------|----------|
| `Ctrl+Shift+X` | Stop tuner | `Ctrl+C` |
| `Ctrl+Shift+R` | Run optimization | Dashboard: `RunOptimization` |
| `Ctrl+Shift+Right` | Next coefficient | Dashboard: `SkipToNextCoefficient` |
| `Ctrl+Shift+Left` | Previous coefficient | Use Backtrack feature |

**Note:** Hotkeys may require elevated permissions on Linux/Mac. If hotkeys don't work, use the fallback options listed above.

**Platform Issues:**
- **Windows:** Hotkeys work without issues
- **Linux/Mac:** May require `sudo` or accessibility permissions
- **ChromeOS:** Hotkey support is limited, use dashboard buttons

For detailed information on troubleshooting hotkey issues, see [HOTKEYS.md](HOTKEYS.md).

## Dashboard Controls

All controls are at `/Tuning/BayesianTuner/` in your dashboard (Shuffleboard/AdvantageKit).

### Runtime Enable/Disable

| Control | Type | Purpose |
|---------|------|---------|
| `TunerEnabled` | Boolean | Turn tuner on/off without restarting |
| `TunerPaused` | Boolean | Shows if tuner is paused (e.g., match mode) |
| `TunerRuntimeStatus` | String | Status: "ACTIVE", "DISABLED", "PAUSED" |

### Action Buttons

| Button | When Visible | Action |
|--------|--------------|--------|
| `RunOptimization` | Autotune is OFF | Manually trigger optimization |
| `SkipToNextCoefficient` | Auto-advance is OFF | Move to next coefficient |

### Status Information

| Field | Shows |
|-------|-------|
| `ShotCount` | Current accumulated shots |
| `CurrentCoefficient` | Which coefficient is being tuned |
| `AutotuneEnabled` | Whether current coefficient uses autotune |
| `AutoAdvanceEnabled` | Whether current coefficient uses auto-advance |
| `ShotThreshold` | Effective threshold for current coefficient |

### Runtime Adjustments

| Control | Purpose |
|---------|---------|
| `NewGlobalThreshold` | Change global shot threshold |
| `UpdateGlobalThreshold` | Button to apply change |
| `NewLocalThreshold` | Change current coefficient's threshold |
| `UpdateLocalThreshold` | Button to apply change |

## Features

### Autotune

**What it does:** Controls WHEN optimization runs

**OFF (Manual):**
- Shots accumulate until you press "Run Optimization"
- Full control over optimization timing
- Good for: Testing, careful tuning, verification

**ON (Automatic):**
- After collecting threshold shots, optimization runs automatically
- No button press needed
- Good for: Fast iteration, long tuning sessions

**Settings:**
```ini
autotune_enabled = True/False
autotune_shot_threshold = 10     # Number of shots
```

### Auto-Advance

**What it does:** Controls WHEN to move to next coefficient

**OFF (Manual):**
- Stays on current coefficient until you press "Skip to Next"
- Full control over progression
- Good for: Thorough tuning, verification

**ON (Automatic):**
- If you get 100% hit rate over threshold shots, advances automatically
- Assumes perfect performance = tuned
- Good for: Fast progression through coefficients

**Settings:**
```ini
auto_advance_on_success = True/False
auto_advance_shot_threshold = 10     # Number of shots
```

### Runtime Enable/Disable

Turn the tuner on or off without restarting the program.

**Dashboard:** Toggle `TunerEnabled`

**When Disabled:**
- No shots are accumulated
- No optimization runs
- Status shows "DISABLED"
- Previous data is preserved

**When Re-Enabled:**
- Resumes from where it left off
- Previous shots still available
- Continues with same coefficient

## Usage Modes

### Mode 1: All Manual (Default)

**Best for:** First-time users, careful tuning

**Configuration:**
```ini
autotune_enabled = False
auto_advance_on_success = False
```

**How it works:**
1. Take shots
2. Press "Run Optimization" when ready
3. Press "Skip to Next" when satisfied
4. Repeat

**Buttons visible:** Both (Run Optimization + Skip)

### Mode 2: Full Automatic

**Best for:** Experienced users, long tuning sessions

**Configuration:**
```ini
autotune_enabled = True
autotune_shot_threshold = 10
auto_advance_on_success = True
auto_advance_shot_threshold = 10
```

**How it works:**
1. Take shots
2. System optimizes every 10 shots automatically
3. System advances when 10/10 shots hit
4. Hands-free operation

**Buttons visible:** None (fully automatic)

### Mode 3: Auto-Optimize, Manual Advance

**Best for:** Trusting optimization but verifying results

**Configuration:**
```ini
autotune_enabled = True
autotune_shot_threshold = 10
auto_advance_on_success = False
```

**How it works:**
1. Take shots
2. System optimizes every 10 shots automatically
3. You press "Skip" when satisfied
4. Good balance of automation and control

**Buttons visible:** Skip only

### Mode 4: Manual Optimize, Auto-Advance

**Best for:** Controlling optimization timing, auto-advance on success

**Configuration:**
```ini
autotune_enabled = False
auto_advance_on_success = True
auto_advance_shot_threshold = 5
```

**How it works:**
1. Take shots
2. Press "Run Optimization" when ready
3. System advances when 5/5 shots hit
4. Control optimization, automatic progression

**Buttons visible:** Run Optimization only

### Mode 5: Different Settings Per Coefficient

**Best for:** Complex tuning scenarios

**Configuration:**

Global (TUNER_TOGGLES.ini):
```ini
autotune_enabled = False           # Manual by default
autotune_force_global = False      # Allow overrides
```

Per-coefficient (COEFFICIENT_TUNING.py):
```python
"kDragCoefficient": {
    "autotune_override": True,     # Enable override
    "autotune_enabled": True,      # Auto for this one
    "autotune_shot_threshold": 20,
}

"kLaunchHeight": {
    "autotune_override": False,    # Use global (manual)
}
```

**Result:** Drag uses automatic (20 shots), launch height uses manual button

## Advanced Features

### Manual Coefficient Adjustment

**Purpose:** Manually set any coefficient value in real-time

**Location:** `/Tuning/BayesianTuner/ManualControl/`

**How to use:**
1. Set `ManualAdjustEnabled = True`
2. Select coefficient from `AvailableCoefficients` list
3. Enter desired value in `NewValue`
4. Check `MinValue`/`MaxValue` for valid range
5. Press `ApplyManualValue` button

**Use cases:**
- Quick testing of specific values
- Resetting to known good value
- Fine-tuning after optimization
- Recovering from bad optimization

**Controls:**

| Control | Purpose |
|---------|---------|
| `ManualAdjustEnabled` | Enable manual adjustment mode |
| `CoefficientSelector` | Choose which coefficient |
| `NewValue` | Enter desired value |
| `ApplyManualValue` | Apply the change |
| `CurrentValue` | Shows current value |
| `MinValue` / `MaxValue` | Valid range |
| `AvailableCoefficients` | List of all coefficients |

### Fine-Tuning Mode

**Purpose:** Adjust WHERE within target you hit (after consistent hits)

**Location:** `/Tuning/BayesianTuner/FineTuning/`

**When to use:** After robot is consistently hitting target, but you want to adjust aim bias

**How to use:**
1. First tune coefficients until consistently hitting
2. Enable `FineTuningEnabled = True`
3. Select direction: `TargetBias` = "LEFT", "RIGHT", "UP", or "DOWN"
4. Set `BiasAmount` (0.0 = center, 1.0 = edge)
5. Take shots and observe

**Example:**
- Want to hit left side of target: `TargetBias = "LEFT"`, `BiasAmount = 0.5`
- Want to hit center: `TargetBias = "CENTER"`, `BiasAmount = 0.0`

**Controls:**

| Control | Purpose |
|---------|---------|
| `FineTuningEnabled` | Enable fine-tuning mode |
| `TargetBias` | Direction: CENTER, LEFT, RIGHT, UP, DOWN |
| `BiasAmount` | 0.0 (center) to 1.0 (edge) |

### Backtrack Tuning

**Purpose:** Go back to re-tune an earlier coefficient

**Location:** `/Tuning/BayesianTuner/Backtrack/`

**When to use:** When later coefficients aren't improving or suspect earlier coefficient was wrong

**How to use:**
1. Enable `BacktrackEnabled = True`
2. Check `TunedCoefficients` to see what's been tuned
3. Set `BacktrackToCoefficient` to the one you want to re-tune
4. Press `TriggerBacktrack` button
5. System resets to that coefficient

**The system logs the interaction** for analysis of coefficient dependencies

**Controls:**

| Control | Purpose |
|---------|---------|
| `BacktrackEnabled` | Allow backtracking |
| `BacktrackToCoefficient` | Which coefficient to return to |
| `TriggerBacktrack` | Execute the backtrack |
| `TunedCoefficients` | List of completed coefficients |
| `TuningOrder` | Full tuning order reference |
| `CurrentCoefficient` | Currently tuning |

### Live Coefficient View

**Purpose:** See current values vs defaults for all coefficients

**Location:** `/Tuning/BayesianTuner/CoefficientsLive/{CoefficientName}/`

**For each coefficient:**

| Field | Shows |
|-------|-------|
| `CurrentValue` | Current operating value |
| `CodeDefault` | Default from config |
| `Difference` | How much changed from default |
| `MinValue` | Minimum allowed value |
| `MaxValue` | Maximum allowed value |
| `Enabled` | Whether being tuned |

## Logging and Data

### Log Files

All logs are saved in `tuner_logs/` directory:

| File | Contents |
|------|----------|
| `bayesian_tuner_YYYYMMDD_HHMMSS.csv` | Shot-by-shot data with all coefficients |
| `coefficient_history_YYYYMMDD.json` | Every coefficient change with timestamp |
| `coefficient_interactions_YYYYMMDD.json` | Detected coefficient dependencies |

### Shot Data CSV

Each row contains:
- Timestamp
- Hit/miss result
- Distance
- Solution (pitch, velocity, yaw)
- All coefficient values at time of shot
- Physical parameters

### Coefficient History JSON

Logs every time a coefficient changes:
- Event type: OPTIMIZATION, MANUAL_CHANGE, BACKTRACK, SESSION_START
- Timestamp
- All coefficient values
- Which coefficient changed

**Use for:**
- Reviewing what values were tried
- Reverting to previous good settings
- Understanding tuning progression

### Interaction Detection

When you backtrack, the system logs a potential interaction between:
- Current coefficient (where you were)
- Target coefficient (where you went back to)

**Use for:**
- Identifying which coefficients affect each other
- Optimizing tuning order
- Understanding system dependencies

## Quick Reference

### Common Tasks

| Want to do this | Do this |
|-----------------|---------|
| Start tuning | Double-click Desktop shortcut |
| Turn on tuner | Toggle `TunerEnabled = True` |
| Run optimization | Press `RunOptimization` (manual mode) |
| Move to next coefficient | Press `SkipToNextCoefficient` (manual mode) |
| Set coefficient value | Use `ManualControl` |
| Adjust aim bias | Use `FineTuning` |
| Go back to earlier coefficient | Use `Backtrack` |
| See current values | Check `CoefficientsLive` |
| Change thresholds | Use `UpdateGlobalThreshold` or `UpdateLocalThreshold` |

### Configuration Quick Guide

| Want this behavior | Set these values |
|--------------------|------------------|
| Manual everything | `autotune_enabled = False`, `auto_advance_on_success = False` |
| Automatic everything | Both enabled with thresholds |
| Manual optimize, auto-advance | `autotune_enabled = False`, `auto_advance_on_success = True` |
| Auto optimize, manual advance | `autotune_enabled = True`, `auto_advance_on_success = False` |
| Same for all coefficients | `force_global = True` |
| Different per coefficient | `force_global = False`, set overrides |

## See Also

- **Setup:** [SETUP.md](SETUP.md) - Installation and setup instructions
- **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common problems and solutions
- **Java Integration:** [JAVA_INTEGRATION.md](JAVA_INTEGRATION.md) - How to integrate with robot code
- **Developer Guide:** [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Architecture and development info
- **Hotkeys:** [HOTKEYS.md](HOTKEYS.md) - Keyboard shortcuts reference
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute to the project
  
