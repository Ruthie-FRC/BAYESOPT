# Troubleshooting Guide

Common issues and solutions for the BayesOpt tuner.

## Table of Contents

- [Setup Issues](#setup-issues)
- [Connection Issues](#connection-issues)
- [Tuner Not Working](#tuner-not-working)
- [Data Issues](#data-issues)
- [Performance Issues](#performance-issues)
- [Getting Help](#getting-help)

## Setup Issues

### Python Not Recognized (Windows)

**Symptom:** Command line says "python is not recognized"

**Cause:** Python not installed or not in PATH

**Solution:**
1. Reinstall Python from [python.org](https://www.python.org/downloads/)
2. ⚠️ **Check "Add Python to PATH"** during installation
3. Restart Command Prompt after installation

**Alternative:** Add Python to PATH manually:
1. Search Windows for "Environment Variables"
2. Click "Environment Variables" button
3. Under "System variables", find "Path"
4. Click "Edit" and add Python installation directory
5. Typical paths: `C:\Python311\` and `C:\Python311\Scripts\`

### Module Not Found Errors

**Symptom:** `ModuleNotFoundError: No module named 'xyz'`

**Cause:** Dependencies not installed

**Solution:**
```bash
# Navigate to repository root
cd /path/to/BAYESOPT

# Install/reinstall dependencies
pip install -r bayesopt/tuner/requirements.txt --upgrade

# If using Python 3 explicitly
pip3 install -r bayesopt/tuner/requirements.txt --upgrade
```

**Common missing modules:**
- `pynetworktables` - NetworkTables library
- `skopt` (scikit-optimize) - Bayesian optimization
- `numpy` - Numerical computing
- `tkinter` - GUI (usually included with Python)

**Linux tkinter fix:**
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

### Window Closes Immediately (Windows)

**Symptom:** Double-clicking shortcut opens window that closes instantly

**Cause:** Error on startup, but window closes before you can see it

**Solution:**
1. Open Command Prompt
2. Navigate to repository: `cd C:\FRC\BAYESOPT`
3. Run manually: `python bayesopt\tuner\main.py`
4. Read the error message
5. Look up specific error in this guide

### Permission Errors (Mac/Linux)

**Symptom:** "Permission denied" when running start script

**Cause:** Script not marked as executable

**Solution:**
```bash
chmod +x START_TUNER.sh
./START_TUNER.sh
```

Or run with Python directly:
```bash
python3 bayesopt/tuner/main.py
```

## Connection Issues

### Cannot Connect to Robot

**Symptom:** GUI shows "Disconnected" in red, or connection status never changes

**Possible Causes & Solutions:**

**1. Laptop not on robot network**
- Verify laptop is connected to robot WiFi or ethernet
- Check WiFi SSID matches your team number
- Try pinging robot: `ping roborio-XXXX-frc.local` (replace XXXX with team number)

**2. Robot not running**
- Verify robot is powered on
- Verify robot code is deployed and running
- Check Driver Station shows robot connection

**3. Wrong robot IP/team number**
- Check NetworkTables configuration
- Default uses team number to find robot
- Try setting explicit IP if team number doesn't work

**4. Firewall blocking connection**
- Windows Firewall may block Python
- Allow Python through firewall
- NetworkTables uses port 5810 (check firewall rules)

**5. NetworkTables version mismatch**
- Ensure robot and laptop use compatible NT versions
- Update pynetworktables: `pip install pynetworktables --upgrade`

### Connection Keeps Dropping

**Symptom:** Connection shows "Connected" then "Disconnected" repeatedly

**Possible Causes:**
- Weak WiFi signal - move laptop closer to robot
- Network congestion - reduce other network traffic
- Robot code restarting - check for robot code issues
- USB issues if using ethernet over USB

**Solution:**
1. Check WiFi signal strength
2. Use ethernet cable if possible
3. Check robot logs for crashes/restarts
4. Reduce dashboard update rate if using Shuffleboard

## Tuner Not Working

### Tuner Enabled But Not Running

**Symptom:** `TunerEnabled = True` but no activity

**Check these:**

**1. Match mode detected**
- Tuner auto-disables during matches (FMS connected)
- Check `TunerRuntimeStatus` - shows "PAUSED" if in match mode
- For tuning, disconnect FMS or use test environment

**2. Invalid data**
- Tuner pauses if receiving bad shot data
- Check logs for "invalid data" warnings
- Verify robot is publishing correct NetworkTables keys
- Verify shot data has valid values (not NaN, not out of range)

**3. Not receiving shots**
- Check robot code calls `logShot()` after each shot
- Verify `ShotTimestamp` is updating in NetworkTables
- Check dashboard for shot count - should increase

### Buttons Not Showing

**Symptom:** "Run Optimization" or "Skip" buttons missing from dashboard

**This is normal!** Buttons only appear when needed:

| Button | Appears When |
|--------|--------------|
| `RunOptimization` | Autotune is OFF (manual mode) |
| `SkipToNextCoefficient` | Auto-advance is OFF (manual mode) |

**If autotune and auto-advance are both ON, no buttons appear** - system runs automatically.

**Check your configuration:**
```ini
# In TUNER_TOGGLES.ini
autotune_enabled = False        # OFF = button appears
auto_advance_on_success = False # OFF = button appears
```

### Optimization Not Improving

**Symptom:** Running optimization but accuracy not improving

**Possible Causes:**

**1. Not enough shots**
- Need sufficient data for optimization
- Try increasing shot threshold
- Take more shots before optimizing

**2. Coefficients at limits**
- Check if suggested values are being clamped to min/max
- Widen ranges in `COEFFICIENT_TUNING.py` if appropriate
- Check logs for "clamped" messages

**3. Wrong coefficient range**
- Min/max may not include optimal value
- Review physics-based estimates for proper ranges
- Consider if default value is way off

**4. Noisy data**
- Inconsistent shooting conditions
- Sensor noise or measurement errors
- Environmental factors (wind, lighting)
- Try more shots per optimization

**5. Coefficient interactions**
- Current coefficient may depend on earlier ones
- Use backtrack feature to re-tune earlier coefficients
- Check interaction logs

### Auto-Advance Not Working

**Symptom:** Getting 100% hits but not advancing

**Check these:**

**1. Feature disabled**
```ini
auto_advance_on_success = True  # Must be True
auto_advance_shot_threshold = 10  # Must have enough shots
```

**2. Not enough consecutive hits**
- Need threshold number of consecutive hits
- Check `ShotCount` vs `auto_advance_shot_threshold`
- One miss resets the counter

**3. Local override**
- Current coefficient may have local settings
- Check per-coefficient config in `COEFFICIENT_TUNING.py`
- Check `AutoAdvanceEnabled` on dashboard

## Data Issues

### Not Receiving Shot Data

**Symptom:** `ShotCount` stays at 0, no data accumulating

**Solutions:**

**1. Robot not publishing data**
- Verify `logShot()` is called after each shot
- Check NetworkTables keys match configuration
- Verify data appears in NetworkTables viewer (Shuffleboard/AdvantageKit)

**2. Wrong NetworkTables paths**
- Default: `/FiringSolver/` for shot data
- Check robot publishes to correct path
- Verify path in COEFFICIENT_TUNING.py matches robot

**3. Shot timestamp not updating**
- Tuner detects new shots by timestamp changes
- Verify `ShotTimestamp` is set to `Timer.getFPGATimestamp()`
- Each shot must have unique timestamp

**4. Java integration not complete**
- See [JAVA_INTEGRATION.md](JAVA_INTEGRATION.md)
- Ensure all required NetworkTables writes are implemented
- Test NetworkTables communication separately

### Invalid/Bad Data

**Symptom:** Logs show "invalid data" warnings, tuner pauses

**Causes:**
- NaN or infinite values
- Out-of-range values
- Missing required fields

**Solutions:**
1. Check sensor data quality
2. Add validation in robot code before publishing
3. Ensure all required fields are published
4. Check for division by zero in calculations

**Required shot data fields:**
- `ShotTimestamp` - Valid FPGA timestamp
- `Hit` - Boolean (true/false)
- `Distance` - Positive number in meters
- `Solution/pitchRadians` - Valid angle
- `Solution/exitVelocity` - Positive number
- `Solution/yawRadians` - Valid angle

## Performance Issues

### Optimization Takes Too Long

**Symptom:** Each optimization cycle takes many seconds

**Solutions:**
1. Reduce number of optimization iterations
2. Reduce complexity of acquisition function
3. Check CPU usage - close other programs
4. Consider reducing bounds on coefficient ranges

### GUI Lag or Freezing

**Symptom:** GUI becomes unresponsive

**Solutions:**
1. Reduce log output verbosity
2. Reduce dashboard update rate
3. Close other resource-intensive programs
4. Check for infinite loops in code

### High Memory Usage

**Symptom:** System running out of memory over time

**Causes:**
- Logs accumulating in memory
- Memory leak in optimization library

**Solutions:**
1. Restart tuner periodically
2. Reduce log retention
3. Update dependencies: `pip install --upgrade -r requirements.txt`

## Getting Help

### Before Asking for Help

1. **Check this guide** for your specific issue
2. **Check logs** in `tuner_logs/` directory
3. **Run unit tests:** `cd bayesopt/tuner && python run_tests.py`
4. **Verify setup** following [SETUP.md](SETUP.md)
5. **Check Java integration** following [JAVA_INTEGRATION.md](JAVA_INTEGRATION.md)

### Information to Provide

When asking for help, include:

1. **Error message** - Exact text of error
2. **What you tried** - Steps you followed
3. **Configuration** - Contents of TUNER_TOGGLES.ini
4. **Environment:**
   - Python version: `python --version`
   - Operating system
   - NetworkTables version
5. **Logs** - Recent entries from tuner log file
6. **Robot connection** - Can you ping robot? See it in Driver Station?

### Where to Get Help

- **GitHub Issues:** Report bugs or ask questions
- **FRC Discord/Forums:** General FRC programming help
- **Documentation:** Review [USER_GUIDE.md](USER_GUIDE.md) and [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

### Contact

- GitHub: [Ruthie-FRC/BAYESOPT](https://github.com/Ruthie-FRC/BAYESOPT)
- Issues: Use GitHub Issues for bug reports and feature requests

## Diagnostic Commands

### Check Python Installation
```bash
python --version
pip --version
```

### Check Dependencies
```bash
pip list | grep pynetworktables
pip list | grep scikit-optimize
pip list | grep numpy
```

### Test NetworkTables Connection
```python
from networktables import NetworkTables
NetworkTables.initialize(server='10.TE.AM.2')  # Replace with your team number
print(NetworkTables.isConnected())
```

### Run Unit Tests
```bash
cd bayesopt/tuner
python run_tests.py
```

### Check Log Files
```bash
# View most recent log
ls -lt tuner_logs/
tail -50 tuner_logs/bayesian_tuner_*.csv
```

### Verify Configuration
```bash
# Check TUNER_TOGGLES.ini
cat bayesopt/config/TUNER_TOGGLES.ini

# Check Python can import modules
python -c "import pynetworktables; print('OK')"
python -c "import skopt; print('OK')"
```

## Common Error Messages

### "NT connection failed"
→ See [Connection Issues](#connection-issues)

### "No module named 'pynetworktables'"
→ See [Module Not Found Errors](#module-not-found-errors)

### "Invalid shot data received"
→ See [Invalid/Bad Data](#invalidbad-data)

### "Coefficient clamped to min/max"
→ Suggested value outside bounds, check ranges in COEFFICIENT_TUNING.py

### "Match mode detected, tuner disabled"
→ FMS connected, disconnect for tuning or use test environment

### "Python is not recognized"
→ See [Python Not Recognized](#python-not-recognized-windows)

## Still Having Issues?

If you've checked everything above and still have issues:

1. **Start fresh:**
   - Re-download repository
   - Reinstall dependencies
   - Use default configuration files

2. **Test components separately:**
   - Test robot NetworkTables independently
   - Test Python dependencies with unit tests
   - Test connection with simple NT script

3. **Ask for help:**
   - Open GitHub issue with details
   - Include all diagnostic information
   - Describe expected vs actual behavior
