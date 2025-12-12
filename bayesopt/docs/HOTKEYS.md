# Keyboard Hotkeys Reference

This document describes all keyboard hotkeys available in the Bayesian Optimization Tuner and their fallback behaviors.

## Overview

The tuner provides keyboard hotkeys for quick access to common functions without needing to use the dashboard. Some hotkeys have fallback options (alternative ways to perform the action), while others require the keyboard library to work.

## Hotkey List

### Stop Tuner
**Hotkey:** `Ctrl+Shift+X`  
**Fallback:** `Ctrl+C` (KeyboardInterrupt)  
**Description:** Stops the tuner gracefully, saving all logs and cleaning up resources.

**Status:** ✅ **Always Available** (has fallback)

If the hotkey registration fails (common on Linux/Mac without elevated permissions), you can always use `Ctrl+C` to stop the tuner.

---

### Run Optimization
**Hotkey:** `Ctrl+Shift+R`  
**Fallback:** Dashboard button: `/Tuning/BayesianTuner/RunOptimization`  
**Description:** Triggers optimization/tuning run on accumulated shots in manual mode.

**Status:** ⚠️ **Hotkey or Dashboard Required**

If the hotkey registration fails, you must use the dashboard button to trigger optimization. This is only needed in manual mode (when `AUTOTUNE_ENABLED = False`).

---

### Next Coefficient
**Hotkey:** `Ctrl+Shift+Right`  
**Fallback:** Dashboard button: `/Tuning/BayesianTuner/SkipToNextCoefficient`  
**Description:** Advances to the next coefficient in the tuning order.

**Status:** ⚠️ **Hotkey or Dashboard Required**

If the hotkey registration fails, you must use the dashboard button to skip to the next coefficient.

---

### Previous Coefficient
**Hotkey:** `Ctrl+Shift+Left`  
**Fallback:** ❌ **None**  
**Description:** Goes back to the previous coefficient in the tuning order.

**Status:** ⚠️ **Hotkey Only** (no fallback available)

If the hotkey registration fails, there is no alternative method to go to the previous coefficient. You would need to use the backtrack feature (`/Tuning/BayesianTuner/Backtrack/`) to select a specific coefficient by name.

---

## Fallback Summary

| Hotkey | Function | Has Fallback? | Fallback Method |
|--------|----------|---------------|-----------------|
| `Ctrl+Shift+X` | Stop Tuner | ✅ Yes | `Ctrl+C` |
| `Ctrl+Shift+R` | Run Optimization | ✅ Yes | Dashboard: `RunOptimization` |
| `Ctrl+Shift+Right` | Next Coefficient | ✅ Yes | Dashboard: `SkipToNextCoefficient` |
| `Ctrl+Shift+Left` | Previous Coefficient | ❌ No | Use Backtrack feature |

---

## Platform-Specific Notes

### Windows
- Hotkeys usually work without issues
- No elevated permissions required

### Linux
- May require running with `sudo` or elevated permissions
- The `keyboard` library needs root access to register global hotkeys
- If hotkeys fail, fallback options are still available

### macOS
- May require granting accessibility permissions to Terminal/Python
- The `keyboard` library needs accessibility access
- If hotkeys fail, fallback options are still available

### ChromeOS/Chromebook
- Hotkey support is limited and may not work at all
- Always use fallback options (dashboard buttons or `Ctrl+C`)

---

## Troubleshooting

### Hotkeys Not Working

**Symptom:** You see warnings like:
```
Failed to register ctrl+shift+x hotkey: [error message]
```

**Solutions:**

1. **Linux/Mac:** Try running with elevated permissions:
   ```bash
   sudo python -m bayesopt.tuner.main
   ```

2. **macOS:** Grant accessibility permissions:
   - System Preferences → Security & Privacy → Privacy → Accessibility
   - Add Terminal or your Python interpreter to the list

3. **Use Fallbacks:** All critical functions have fallback options via dashboard buttons or `Ctrl+C`

### Hotkey Conflicts

If a hotkey conflicts with your system or another application:

1. The tuner will show which hotkeys registered successfully at startup
2. Use the fallback options for any hotkeys that failed to register
3. You can modify the hotkey definitions in `bayesopt/tuner/tuner.py` if needed

---

## Technical Details

### Keyboard Library

The tuner uses the `keyboard` library (version >= 0.13.5) to register global hotkeys. This library:

- Requires root/admin privileges on Linux/Mac
- Works without special permissions on Windows
- May have limited support on some platforms

### Hotkey Registration

At startup, the tuner attempts to register all hotkeys:

- If registration succeeds, the hotkey is active
- If registration fails, a warning is logged
- The tuner displays which hotkeys are available
- Fallback options remain available regardless

### Hotkey Cleanup

When the tuner stops, all registered hotkeys are automatically removed to prevent conflicts with other applications.

---

## Advanced Usage

### Customizing Hotkeys

To customize hotkey combinations, edit the constants at the top of `bayesopt/tuner/tuner.py`:

```python
# Keyboard hotkeys
STOP_HOTKEY = 'ctrl+shift+x'
RUN_OPTIMIZATION_HOTKEY = 'ctrl+shift+r'
NEXT_COEFFICIENT_HOTKEY = 'ctrl+shift+right'
PREV_COEFFICIENT_HOTKEY = 'ctrl+shift+left'
```

Valid key combinations include:
- `ctrl+shift+letter`
- `ctrl+alt+letter`
- `ctrl+shift+arrow_key`
- And many other combinations supported by the `keyboard` library

### Adding New Hotkeys

To add a new hotkey:

1. Define the hotkey constant in `tuner.py`
2. Create a callback function in `run_tuner()`
3. Register the hotkey with `keyboard.add_hotkey()`
4. Add cleanup in the `finally` block
5. Update this documentation

---

## See Also

- **User Guide:** [USER_GUIDE.md](USER_GUIDE.md) - General usage instructions
- **Dashboard Controls:** [USER_GUIDE.md#dashboard-controls](USER_GUIDE.md#dashboard-controls) - Alternative to hotkeys
- **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- **Setup:** [SETUP.md](SETUP.md) - Installation instructions
  
