# Setup Guide

Complete setup instructions for the BayesOpt tuner on all platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Windows Setup](#windows-setup)
- [Mac/Linux Setup](#maclinux-setup)
- [Installing Dependencies](#installing-dependencies)
- [Verifying Installation](#verifying-installation)
- [Next Steps](#next-steps)

## Prerequisites

Before you begin, you need:

1. **Python 3.8 or newer** installed on your Driver Station laptop
2. **The laptop must be able to connect** to your robot's network (WiFi or Ethernet)
3. **Your robot code must be integrated** with NetworkTables (see [JAVA_INTEGRATION.md](JAVA_INTEGRATION.md))

## Windows Setup

### Step 1: Install Python

If Python is not already installed:

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click **"Download Python 3.x.x"** (the big yellow button)
3. Run the installer
4. ⚠️ **IMPORTANT:** Check the box that says **"Add Python to PATH"** at the bottom!
5. Click **"Install Now"**

**Verify Python is installed:**
```cmd
python --version
```
You should see something like `Python 3.11.5`

### Step 2: Download the Code

**Option A: Clone with Git (Recommended)**
```cmd
git clone https://github.com/Ruthie-FRC/BAYESOPT.git
cd BAYESOPT
```

**Option B: Download ZIP**
1. Go to the GitHub repository
2. Click the green **"Code"** button
3. Click **"Download ZIP"**
4. Extract to a folder (e.g., `C:\FRC\BAYESOPT`)

### Step 3: Install Dependencies

Open Command Prompt and run:
```cmd
cd C:\FRC\BAYESOPT
pip install -r bayesopt/tuner/requirements.txt
```

Wait for all packages to install. This only needs to be done once.

### Step 4: Create Desktop Shortcut

1. Open **File Explorer**
2. Navigate to the BAYESOPT folder (e.g., `C:\FRC\BAYESOPT`)
3. **Double-click** `CREATE_DESKTOP_SHORTCUT.bat`
4. A shortcut called **"BayesOpt Tuner"** will appear on your Desktop!

### Step 5: Run the Tuner

From now on, to start the tuner:

1. Make sure your laptop is connected to the robot's network
2. **Double-click the "BayesOpt Tuner" shortcut** on your Desktop
3. A GUI window will appear showing connection status

**Alternative:** You can also double-click `START_TUNER.bat` in the BAYESOPT folder.

## Mac/Linux Setup

### Step 1: Check Python Version

Most Mac and Linux systems come with Python. Check your version:
```bash
python3 --version
```

If you need to install Python:
- **Mac:** Download from [python.org](https://www.python.org/downloads/) or use Homebrew: `brew install python`
- **Linux:** Use your package manager, e.g., `sudo apt install python3 python3-pip`

### Step 2: Download the Code

```bash
git clone https://github.com/Ruthie-FRC/BAYESOPT.git
cd BAYESOPT
```

### Step 3: Install Dependencies

```bash
pip3 install -r bayesopt/tuner/requirements.txt
```

Or if you have a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r bayesopt/tuner/requirements.txt
```

### Step 4: Make Start Script Executable

```bash
chmod +x START_TUNER.sh
```

### Step 5: Run the Tuner

```bash
./START_TUNER.sh
```

Or run directly with Python:
```bash
python3 bayesopt/tuner/main.py
```

## Installing Dependencies

The tuner requires these Python packages (automatically installed by requirements.txt):

- `pynetworktables` - NetworkTables communication
- `scikit-optimize` - Bayesian optimization
- `numpy` - Numerical computations
- `tkinter` - GUI (usually included with Python)

**If you encounter "module not found" errors:**
```bash
pip install -r bayesopt/tuner/requirements.txt --upgrade
```

**On Linux, if tkinter is missing:**
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

## Verifying Installation

### Run Unit Tests

To verify everything is working correctly:

```bash
cd bayesopt/tuner
python run_tests.py
```

**Expected output:** All tests should pass ✅

If tests fail, check:
1. Python version is 3.8 or newer
2. All dependencies are installed
3. You're in the correct directory

### Test NetworkTables Connection

1. Start your robot (or robot simulator)
2. Run the tuner
3. Check the GUI window for connection status
4. Look for "Connected" in green

If connection fails, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Next Steps

After successful setup:

1. **Integrate Java code:** Follow [JAVA_INTEGRATION.md](JAVA_INTEGRATION.md) to add NetworkTables support to your robot
2. **Configure tuner:** Edit `bayesopt/config/TUNER_TOGGLES.ini` for your preferences
3. **Learn features:** Read [USER_GUIDE.md](USER_GUIDE.md) for complete documentation
4. **Start tuning:** See the [Quick Start](#quick-start) section in the main README

## Common Setup Issues

### "Python is not recognized" (Windows)

**Problem:** Python not in PATH

**Solution:** 
1. Reinstall Python
2. Make sure to check **"Add Python to PATH"** during installation
3. Or add manually: Search "Environment Variables" → Edit PATH → Add Python directory

### "Cannot connect to robot"

**Problem:** Laptop not on robot network or robot not running

**Solution:**
1. Verify laptop is connected to robot WiFi/Ethernet
2. Verify robot is powered on and running code
3. Check robot IP address in config (default: team number based)
4. Ping the robot: `ping roborio-TEAM-frc.local`

### "Module not found" errors

**Problem:** Dependencies not installed or wrong Python version

**Solution:**
```bash
# Make sure you're using the right Python
python --version  # or python3 --version

# Reinstall dependencies
pip install -r bayesopt/tuner/requirements.txt --force-reinstall
```

### Window closes immediately (Windows)

**Problem:** Error on startup

**Solution:**
1. Open Command Prompt
2. Navigate to BAYESOPT folder
3. Run manually: `python bayesopt\tuner\main.py`
4. Read the error message
5. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for specific error fixes

### Permission errors (Mac/Linux)

**Problem:** Script not executable or permission denied

**Solution:**
```bash
# Make script executable
chmod +x START_TUNER.sh

# Or run with Python directly
python3 bayesopt/tuner/main.py
```

## Additional Resources

- **Java Integration:** [JAVA_INTEGRATION.md](JAVA_INTEGRATION.md)
- **User Guide:** [USER_GUIDE.md](USER_GUIDE.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Development:** [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
