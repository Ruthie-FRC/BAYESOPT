#!/usr/bin/env python3
"""
Unit Test Runner for the Bayesian Tuner.

This script runs all unit tests for the BayesOpt tuner module.

WHAT ARE UNIT TESTS?
--------------------
Unit tests are automated tests that verify small pieces of code work correctly.
They test individual functions/classes in isolation without needing real hardware.

TESTS INCLUDED:
- test_config.py: Tests configuration loading and validation
- test_logger.py: Tests CSV logging and coefficient history tracking
- test_optimizer.py: Tests Bayesian optimization and coefficient tuning logic

HOW TO RUN:
-----------
From the tuner directory:
    python run_tests.py

Or from anywhere:
    python -m bayesopt.tuner.run_tests

WHEN TO RUN:
-----------
- Before deploying to robot (to catch bugs early)
- After making any code changes
- To verify the tuner will work correctly on the robot
"""

import sys
import unittest
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    """Discover and run all tests."""
    # Discover tests in the tests directory
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on results
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
# ----------------------------------------------------------------------
