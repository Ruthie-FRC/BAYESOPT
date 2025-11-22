# Troubleshooting — Why it's not turning on

Why it's not turning on — checklist and fixes

**FOR DRIVERS**

- make sure everyhting is turned on
- make sure everything is plugged in

If still failing, ask a programmer for assistance.

**FOR PROGRAMMERS**

Do the following:

1. TUNER_ENABLED is false
   - Fix: set TUNER_ENABLED = True in TUNER_TOGGLES.ini or TunerConfig before starting.

2. Missing/incorrect NT server IP or team number
   - Symptom: "NT connect failed" in daemon log or no NT connection.
   - Fix: set correct NT_SERVER_IP or TEAM_NUMBER in config and restart.

3. Dependencies missing
   - Symptom: ImportError or ModuleNotFoundError on startup.
   - Fix: pip install -r bayesopt/tuner/requirements.txt

4. Running in match mode (FMS detected)
   - Symptom: Tuner auto-disables immediately; logs show match-mode detected.
   - Fix: For tuning, ensure FMS is not connected or use a test environment.

5. NT keys mismatch with robot
   - Symptom: No shot data; read_shot_data returns None or invalid values.
   - Fix: Confirm robot publishes the same NetworkTables keys (see COEFFICIENT_TUNING.py nt_key fields).

6. Permissions or missing log directory
   - Symptom: File write errors when creating tuner_logs.
   - Fix: Ensure LOG_DIRECTORY exists and is writable; adjust path in config.

7. Invalid shot data / too noisy
   - Symptom: optimizer receives invalid readings, tuning pauses.
   - Fix: Verify robot's shot logger (LogHit/LogMiss buttons), add sensors needed, or increase MIN_VALID_SHOTS_BEFORE_UPDATE.

8. Coefficients clamped to same value (no change)
   - Symptom: Suggested values repeatedly clamped to min/max.
   - Fix: Check COEFFICIENT_TUNING ranges; widen sensible ranges or correct default value.

9. Optimizer not converging
   - Symptom: Iterations run but no progress.
   - Fixes:
     - Increase N_CALLS_PER_COEFFICIENT
     - Increase N_INITIAL_POINTS
     - Verify shot quality and increase MIN_VALID_SHOTS_BEFORE_UPDATE
     - Review initial_step_size and step_decay_rate

10. Port or firewall issues blocking NT
    - Symptom: NT connection stalls, partial writes.
    - Fix: Ensure network allows UDP/TCP used by NetworkTables between DS PC and robot.

If still failing
- Inspect daemon log for the first ERROR/TRACE message and follow that code path.
- Run unit tests to ensure core modules load correctly.
- If NT issues persist, isolate with a local NT server emulator.
- Use logs and CSVs to identify whether the issue is NT, data quality, or optimizer-related.
- Ask either Ruthie or Michael 
