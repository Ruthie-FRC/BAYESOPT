#!/usr/bin/env python3
"""
AUTO-START TUNER DAEMON

This script runs automatically in the background when the Driver Station starts.
Programmers set TUNER_ENABLED in config, drivers do NOTHING.

To set up auto-start:
  Windows: Add to Startup folder or Task Scheduler
  Mac: Add to Login Items
  Linux: Add to systemd or cron @reboot
"""

import sys
import os
import time
import configparser

# Add parent directory (bayesopt) to path to import tuner module
script_dir = os.path.dirname(os.path.abspath(__file__))
bayesopt_dir = os.path.dirname(script_dir)
sys.path.insert(0, bayesopt_dir)

from tuner import BayesianTunerCoordinator, TunerConfig, setup_logging
import logging


def load_config_from_file():
    """Load configuration from tuner_config.ini file."""
    config_file = os.path.join(os.path.dirname(__file__), 'tuner_config.ini')
    
    # Defaults if no config file
    if not os.path.exists(config_file):
        return {
            'enabled': False, 
            'team_number': 0,
            'require_shot_logged': False,
            'require_coefficients_updated': False
        }
    
    try:
        parser = configparser.ConfigParser()
        parser.read(config_file)
        
        enabled = parser.getboolean('tuner', 'enabled', fallback=False)
        team_number = parser.getint('tuner', 'team_number', fallback=0)
        
        # Read shooting interlock settings
        require_shot_logged = parser.getboolean('shooting_interlocks', 'require_shot_logged', fallback=False)
        require_coefficients_updated = parser.getboolean('shooting_interlocks', 'require_coefficients_updated', fallback=False)
        
        return {
            'enabled': enabled,
            'team_number': team_number,
            'require_shot_logged': require_shot_logged,
            'require_coefficients_updated': require_coefficients_updated,
        }
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {
            'enabled': False, 
            'team_number': 0,
            'require_shot_logged': False,
            'require_coefficients_updated': False
        }


def main():
    """Main daemon loop."""
    
    # Silent logging to file only
    log_file = os.path.join(os.path.dirname(__file__), 'tuner_logs', 'tuner_daemon.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Tuner Daemon Started")
    logger.info("=" * 60)
    
    # Load configuration
    settings = load_config_from_file()
    
    if not settings['enabled']:
        logger.info("Tuner is DISABLED in config - daemon will not start tuner")
        logger.info("Programmers: Set enabled = True in tuner_config.ini")
        # Daemon stays running but doesn't do anything
        # This way it's always ready if programmers enable it
        while True:
            time.sleep(60)  # Check every minute if config changed
            new_settings = load_config_from_file()
            if new_settings['enabled']:
                settings = new_settings
                break
    
    logger.info(f"Tuner ENABLED - Team {settings['team_number']}")
    logger.info(f"Interlock settings: require_shot_logged={settings['require_shot_logged']}, "
               f"require_coefficients_updated={settings['require_coefficients_updated']}")
    
    # Calculate robot IP
    team_number = settings['team_number']
    if team_number > 0:
        team_str = str(team_number).zfill(4)
        server_ip = f"10.{team_str[:2]}.{team_str[2:]}.2"
    else:
        # Try common addresses
        server_ip = None  # Auto-detect
    
    logger.info(f"Target robot IP: {server_ip or 'auto-detect'}")
    
    # Create tuner config with interlock settings
    config = TunerConfig()
    config.TUNER_ENABLED = True
    config.REQUIRE_SHOT_LOGGED = settings['require_shot_logged']
    config.REQUIRE_COEFFICIENTS_UPDATED = settings['require_coefficients_updated']
    if server_ip:
        config.NT_SERVER_IP = server_ip
    
    # Start tuner coordinator
    try:
        logger.info("Starting tuner coordinator...")
        coordinator = BayesianTunerCoordinator(config)
        coordinator.start(server_ip=server_ip)
        
        logger.info("Tuner running in background")
        logger.info("Drivers don't need to do anything!")
        
        # Keep running until interrupted
        while True:
            time.sleep(10)
            
            # Check if we should reload config
            new_settings = load_config_from_file()
            if not new_settings['enabled'] and settings['enabled']:
                logger.info("Tuner disabled in config - stopping")
                coordinator.stop()
                settings = new_settings
                # Wait for re-enable
                while True:
                    time.sleep(60)
                    newer_settings = load_config_from_file()
                    if newer_settings['enabled']:
                        logger.info("Tuner re-enabled - restarting")
                        coordinator.start(server_ip=server_ip)
                        settings = newer_settings
                        break
            
    except KeyboardInterrupt:
        logger.info("Daemon stopped by signal")
        if 'coordinator' in locals():
            coordinator.stop()
    except Exception as e:
        logger.error(f"Daemon error: {e}", exc_info=True)
        if 'coordinator' in locals():
            coordinator.stop()


if __name__ == "__main__":
    main()
    