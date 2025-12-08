#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  BAYESIAN OPTIMIZATION TUNER - MAIN ENTRY POINT
  
  This is the main script that runs on your LAPTOP (not the RoboRIO).
  It connects to the robot via NetworkTables and performs all optimization
  calculations locally, then sends the updated coefficients to the robot.
  
  HOW TO RUN:
    Windows: Double-click START_TUNER.bat
    Mac/Linux: Double-click START_TUNER.sh (may need to chmod +x first)
    
  Or from command line:
    python -m bayesopt.tuner.main
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import time
import signal

# Add parent directory to path for imports
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bayesopt.tuner.config import TunerConfig
from bayesopt.tuner.tuner import BayesianTunerCoordinator


def print_banner():
    """Print startup banner."""
    print()
    print("═" * 75)
    print("  BAYESIAN OPTIMIZATION TUNER")
    print("  Running on your laptop - connecting to robot via NetworkTables")
    print("═" * 75)
    print()


def print_dashboard_info():
    """Print dashboard control information."""
    print("Dashboard Controls at /Tuning/BayesianTuner/:")
    print("┌─────────────────────────────┬─────────────────────────────────────────┐")
    print("│ Control                     │ Description                             │")
    print("├─────────────────────────────┼─────────────────────────────────────────┤")
    print("│ TunerEnabled                │ Toggle entire system on/off             │")
    print("│ RunOptimization             │ Manual trigger (when autotune OFF)      │")
    print("│ SkipToNextCoefficient       │ Skip to next (when auto-advance OFF)    │")
    print("│ ManualControl/              │ Manually adjust any coefficient         │")
    print("│ FineTuning/                 │ Adjust aim bias (LEFT, RIGHT, etc.)     │")
    print("│ Backtrack/                  │ Re-tune earlier coefficients            │")
    print("│ CoefficientsLive/           │ View current vs default values          │")
    print("└─────────────────────────────┴─────────────────────────────────────────┘")
    print()


def main():
    """Main entry point for the Bayesian Optimization Tuner."""
    print_banner()
    
    # Load configuration
    print("Loading configuration...")
    try:
        config = TunerConfig()
        print(f"  ✓ Loaded {len(config.COEFFICIENTS)} coefficients")
        print(f"  ✓ Tuning order: {config.TUNING_ORDER}")
    except Exception as e:
        print(f"  ✗ ERROR loading configuration: {e}")
        print("  Check that TUNER_TOGGLES.ini and COEFFICIENT_TUNING.py exist")
        input("\nPress Enter to exit...")
        return 1
    
    # Initialize tuner
    print("\nInitializing tuner...")
    try:
        tuner = BayesianTunerCoordinator(config)
        print("  ✓ Tuner initialized")
        print(f"  ✓ Logs will be saved to: {tuner.data_logger.log_directory}")
    except Exception as e:
        print(f"  ✗ ERROR initializing tuner: {e}")
        input("\nPress Enter to exit...")
        return 1
    
    # Connect to NetworkTables and start tuner
    print("\nConnecting to robot via NetworkTables...")
    print("  Make sure:")
    print("  1. Robot is powered on")
    print("  2. Laptop is connected to robot network")
    print("  3. Robot code is running")
    print()
    
    try:
        tuner.start()
        if tuner.nt_interface.is_connected():
            print("  ✓ Connected to NetworkTables!")
        else:
            print("  ⚠ Connection pending...")
            print("  Will keep trying to connect...")
    except Exception as e:
        print(f"  ✗ ERROR starting tuner: {e}")
        print("  Will keep trying to connect...")
    
    # Print dashboard info
    print()
    print_dashboard_info()
    
    # Setup graceful shutdown
    running = True
    def signal_handler(sig, frame):
        nonlocal running
        print("\n\nShutting down gracefully...")
        running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Main loop - just wait for shutdown since tuner runs in its own thread
    print("Tuner is running! Press Ctrl+C to stop.")
    print("=" * 75)
    print()
    
    try:
        while running:
            time.sleep(1)
    finally:
        print("\nSaving logs and cleaning up...")
        try:
            tuner.stop()
            print("  ✓ Cleanup complete")
        except Exception as e:
            print(f"  ✗ Error during cleanup: {e}")
    
    print("\nTuner stopped. Goodbye!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
    
