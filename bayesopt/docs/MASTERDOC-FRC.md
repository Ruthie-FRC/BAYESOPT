# Bayesian Optimization Tuner — Master Developer Document

**THIS IS NOT A HOW TO OPERATE GUIDE. THIS IS A MASTERDOC.** 
**IT CONTAINS LOGIC AND EXPLINATIONS NOT NESSCARY FOR OPERATION.**
**THE OPERATION GUIDE IS START.md.**
**THIS IS NOT REQUIRED READING.**

Why I made this document
- Single-source, practical reference for maintainers. Explains architecture, runtime flow, interactions, and exactly where to change things.

Quick summary (of how i have it set up. if you are not using this 
for FRC purposes, please read MASTERDOC-APP for non FRC applications)
- Runs on a Driver Station or dev host, reads shot feedback via NetworkTables (NT), and uses a per-coefficient Bayesian optimizer to propose safe coefficient updates. Tunes one coefficient at a time in a configured priority order. Safety: clamping, rate-limits, match-mode disable, invalid-data handling.

Bayesian optimization — quick primer
- Bayesian optimization is a sample-efficient method for tuning expensive or noisy black‑box functions: it builds a probabilistic surrogate (commonly a Gaussian Process) of the objective and uses an acquisition function to pick the next promising point, balancing exploration vs. exploitation.
- In this project the tuner treats robot "shot" performance as the objective: the optimizer proposes safe coefficient changes, receives shot scores as feedback, and updates its surrogate to suggest improved coefficients over time.

architecture (compact flow)
- Components:
  - Launcher: scripts/{RUN_TUNER.sh,RUN_TUNER.bat,tuner_daemon.py}
  - Coordinator: tuner/tuner.py
  - NT layer: tuner/nt_interface.py
  - Optimizer: tuner/optimizer.py
  - Config: bayesopt/config/* + tuner/config.py
  - Logging: tuner/logger.py
  - Tests: tuner/tests/*

Flow (simple diagram):

[Launcher]
   |
   v
[Coordinator — tuner/tuner.py]
   |--> [nt_interface.py]   (NetworkTables reads/writes)
   |--> [optimizer.py]      (suggest_next_value, report_result)
   `--> [logger.py]         (logging & CSV)
   
Data path:
nt_interface.read_shot_data() --> Coordinator --> optimizer.suggest_next_value()
optimizer.report_result(...) --> Coordinator --> nt_interface.write_coefficient(...)
logger.log_shot() <--- Coordinator / optimizer / nt_interface

Detailed data flow (step-by-step)
1. Launcher starts the daemon (tuner_daemon.py) which constructs TunerConfig and starts Coordinator.
2. Coordinator loop (tuner.py) polls nt_interface.read_shot_data() at TUNER_UPDATE_RATE_HZ.
3. Each ShotData is validated (physically plausible fields). Invalid samples increment a counter; pause when threshold exceeded.
4. Valid samples are sent to the active CoefficientTuner (optimizer.py) which maintains a GP model and suggests_next_value().
5. Coordinator clamps the suggestion to COEFFICIENT_TUNING bounds and enforces min_write_interval per-coefficient.
6. Coordinator calls nt_interface.write_coefficient(name, value).
7. Shot outcomes are reported back to optimizer.report_result(value, score) to update the surrogate.
8. logger.log_shot() and log_event() record inputs, suggestions, results, and state changes.

Where logic lives (file map + responsibilities)
- bayesopt/config/COEFFICIENT_TUNING.py
  - Define each coefficient: nt_path/key, min, max, initial, step, safe_delta, convergence params.
  - Set TUNING_ORDER (array of coefficient names).
  - Change here to add coefficients or modify ranges.
- bayesopt/config/TUNER_TOGGLES.ini
  - Global on/off toggles and runtime defaults.
- bayesopt/scripts/RUN_TUNER.sh, RUN_TUNER.bat, tuner_daemon.py
  - Process/daemon start-up logic. Modify for autostart/system integration.
- bayesopt/tuner/config.py
  - Loads and validates effective runtime configuration (typed fields). Change to add runtime flags or new config validation.
- bayesopt/tuner/nt_interface.py
  - Encapsulates all NetworkTables reads/writes and connection handling:
    - connect(), read_shot_data(), write_coefficient(name, value), is_match_mode().
  - To change NT key names or add new NT telemetry, update here and COEFFICIENT_TUNING.py.
- bayesopt/tuner/optimizer.py
  - BayesianOptimizer / CoefficientTuner classes:
    - suggest_next_value(), report_result(value, score), is_converged().
  - Swap surrogate model here while keeping the public interface.
- bayesopt/tuner/tuner.py
  - Coordinator: scheduling, safety checks (match mode, invalid-data), enforcing clamping/rate-limits, sequencing TUNING_ORDER.
  - Primary place to adjust orchestration logic.
- bayesopt/tuner/logger.py
  - CSV and daemon logging. Single place to add/remove fields or change formats.
- bayesopt/tuner/tests/*
  - Unit tests that mock nt_interface and validate config, optimizer, and coordinator behavior.
- bayesopt/tuner/requirements.txt
  - Add runtime dependencies (skopt, numpy, etc).

Interaction matrix (who calls whom)
- tuner_daemon.py -> tuner.Tuner (start/stop)
- tuner.Tuner -> nt_interface, optimizer, logger, config
- optimizer -> logger (for debug events)
- nt_interface -> logger (connection events)
- Tests -> mock nt_interface to exercise tuner and optimizer

Change guidance (what to edit for common tasks)
- Add/modify coefficient:
  1) Edit COEFFICIENT_TUNING.py: add CoefficientConfig and update TUNING_ORDER.
  2) Update unit tests in tuner/tests/ to cover clamping and optimizer behavior.
  3) If NT key names changed, modify nt_interface.py accordingly.
- Change optimizer algorithm:
  - Implement new model in optimizer.py keeping suggest_next_value/report_result/is_converged API and update tests.
- Add runtime toggle:
  - Add the toggle to TUNER_TOGGLES.ini and reflect default/validation in tuner/config.py.
- Change logging fields:
  - Update logger._initialize_csv_log() header and logger.log_shot(); update tests to validate columns.
- Integrate with different data source:
  - Replace nt_interface.py implementation but keep the same external methods used by tuner.py.

Safety & operational rules (explicit)
- Match-mode disable: if nt_interface.is_match_mode() is True, tuner must not write coefficients.
- Clamping: enforce [min,max] from COEFFICIENT_TUNING for every write.
- Rate-limiting: enforce min_write_interval per-coefficient; configurable in tuner/config.py.
- Invalid data: define max_bad_samples; on exceed, pause tuning until sufficient good samples appear.
- Graceful shutdown: tuner.stop() flushes logs and closes NT connection.

Flowchart for state transitions (ASCII)

[IDLE] --start--> [TUNING_LOOP]
[TUNING_LOOP] --match_mode_on--> [DISABLED]
[TUNING_LOOP] --invalid_data--> [PAUSED]
[PAUSED] --good_data_restored--> [TUNING_LOOP]
[TUNING_LOOP] --converged_current_coeff--> [NEXT_COEFFICIENT or COMPLETE]
[ANY] --stop/exit--> [SHUTDOWN]

Testing strategy
- Unit tests must run offline and mock NT:
  - Mock nt_interface.read_shot_data() to feed deterministic synthetic data.
  - Assert clamping: suggested values outside bounds are clamped before nt_interface.write_coefficient() is called.
  - Assert rate-limiting: repeated suggestions within the min interval do not trigger writes.
  - Optimizer tests: feed synthetic rewards and assert the optimizer model updates and converges.
- run_tests.py executes all unit tests (tuner/tests/*).

Debugging checklist
- Is NT connected? Check nt_interface logs and connection state.
- Is tuner disabled due to match-mode? nt_interface.is_match_mode()
- Are writes being throttled? Check timestamps in logs and min_write_interval.
- Is optimizer receiving results? Check logger entries for report_result events.
- Use DEBUG logging: setup_logging(config, log_level=logging.DEBUG)
