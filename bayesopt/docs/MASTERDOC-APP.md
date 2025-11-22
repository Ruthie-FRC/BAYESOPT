# Bayesian Optimization Tuner — Master Developer Document (Application-Agnostic)

Note to educators and researchers:
- If you are a professor, college, or academic institution, I would be happy to configure or adjust this project to your needs (different data sources, alternate coefficients, experimental workflows, etc.). Contact me to discuss integrations or dataset-specific tuning.

Open source and attribution:
- This project is released as open source and is free to use. I do not expect nor want financial compensation for its use. If you incorporate or adapt this work, please credit the original author(s) in documentation or acknowledgements — attribution is appreciated as it reflects the time invested in development.

Purpose
- Single-source, practical reference for maintainers. Explains architecture, runtime flow, interactions, and exactly where to change things.
- This is a developer/master doc, not an operator guide. See START.md (or equivalent) for operational instructions.

Quick summary
- Runs on a host or embedded dev machine, reads performance/telemetry via a telemetry layer (e.g., NetworkTables, MQTT, REST), and uses per-coefficient Bayesian optimizers to propose safe coefficient updates. Tunes one coefficient at a time in a configurable priority order. Safety: clamping, rate-limits, experimental-mode disable, invalid-data handling.

Bayesian optimization — quick primer
- Bayesian optimization is a sample-efficient method for tuning expensive or noisy black‑box functions: it builds a probabilistic surrogate (commonly a Gaussian Process) of the objective and uses an acquisition function to pick the next promising point, balancing exploration vs. exploitation.
- In this project the tuner treats measured performance (for example: shot score, control error, or other task metric) as the objective: the optimizer proposes safe coefficient changes, receives feedback as scores, and updates its surrogate to suggest improved coefficients over time.

Architecture (compact flow)
- Components:
  - Launcher: scripts/{RUN_TUNER.sh,RUN_TUNER.bat,tuner_daemon.py}
  - Coordinator: tuner/tuner.py
  - Telemetry layer: tuner/nt_interface.py (abstracts NetworkTables or other telemetry systems)
  - Optimizer: tuner/optimizer.py
  - Config: bayesopt/config/* + tuner/config.py
  - Logging: tuner/logger.py
  - Tests: tuner/tests/*

Flow (simple diagram):

[Launcher]
   |
   v
[Coordinator — tuner/tuner.py]
   |--> [telemetry interface]   (telemetry reads/writes)
   |--> [optimizer.py]          (suggest_next_value, report_result)
   `--> [logger.py]             (logging & CSV)
   
Data path:
telemetry_interface.read_sample() --> Coordinator --> optimizer.suggest_next_value()
optimizer.report_result(...) --> Coordinator --> telemetry_interface.write_coefficient(...)
logger.log_shot() <--- Coordinator / optimizer / telemetry_interface

Detailed data flow (step-by-step)
1. Launcher starts the daemon which constructs TunerConfig and starts the Coordinator.
2. Coordinator loop (tuner.py) polls telemetry_interface.read_sample() at TUNER_UPDATE_RATE_HZ.
3. Each Sample is validated (physically plausible fields). Invalid samples increment a counter; pause when threshold exceeded.
4. Valid samples are sent to the active CoefficientTuner (optimizer.py) which maintains a surrogate model and suggest_next_value().
5. Coordinator clamps the suggestion to COEFFICIENT_TUNING bounds and enforces min_write_interval per-coefficient.
6. Coordinator calls telemetry_interface.write_coefficient(name, value).
7. Sample outcomes are reported back to optimizer.report_result(value, score) to update the surrogate.
8. logger.log_shot() and log_event() record inputs, suggestions, results, and state changes.

Where logic lives (file map + responsibilities)
- bayesopt/config/COEFFICIENT_TUNING.py
  - Define each coefficient: telemetry key, min, max, initial, step, safe_delta, convergence params.
  - Set TUNING_ORDER (array of coefficient names).
  - Change here to add coefficients or modify ranges.
- bayesopt/config/TUNER_TOGGLES.ini
  - Global on/off toggles and runtime defaults.
- bayesopt/scripts/RUN_TUNER.sh, RUN_TUNER.bat, tuner_daemon.py
  - Process/daemon start-up logic. Modify for autostart/system integration.
- bayesopt/tuner/config.py
  - Loads and validates effective runtime configuration (typed fields). Change to add runtime flags or new config validation.
- bayesopt/tuner/nt_interface.py (telemetry interface)
  - Encapsulates telemetry reads/writes and connection handling:
    - connect(), read_sample(), write_coefficient(name, value), is_experiment_mode().
  - To change telemetry key names or add new telemetry, update here and COEFFICIENT_TUNING.py.
- bayesopt/tuner/optimizer.py
  - BayesianOptimizer / CoefficientTuner classes:
    - suggest_next_value(), report_result(value, score), is_converged().
  - Swap surrogate model here while keeping the public interface.
- bayesopt/tuner/tuner.py
  - Coordinator: scheduling, safety checks (experiment-mode disable, invalid-data), enforcing clamping/rate-limits, sequencing TUNING_ORDER.
  - Primary place to adjust orchestration logic.
- bayesopt/tuner/logger.py
  - CSV and daemon logging. Single place to add/remove fields or change formats.
- bayesopt/tuner/tests/*
  - Unit tests that mock the telemetry interface and validate config, optimizer, and coordinator behavior.
- bayesopt/tuner/requirements.txt
  - Add runtime dependencies (skopt, numpy, etc).

Interaction matrix (who calls whom)
- tuner_daemon.py -> tuner.Tuner (start/stop)
- tuner.Tuner -> telemetry_interface, optimizer, logger, config
- optimizer -> logger (for debug events)
- telemetry_interface -> logger (connection events)
- Tests -> mock telemetry_interface to exercise tuner and optimizer

Change guidance (what to edit for common tasks)
- Add/modify coefficient:
  1) Edit COEFFICIENT_TUNING.py: add CoefficientConfig and update TUNING_ORDER.
  2) Update unit tests in tuner/tests/ to cover clamping and optimizer behavior.
  3) If telemetry key names changed, modify telemetry_interface (nt_interface.py) accordingly.
- Change optimizer algorithm:
  - Implement new model in optimizer.py keeping suggest_next_value/report_result/is_converged API and update tests.
- Add runtime toggle:
  - Add the toggle to TUNER_TOGGLES.ini and reflect default/validation in tuner/config.py.
- Change logging fields:
  - Update logger._initialize_csv_log() header and logger.log_shot(); update tests to validate columns.
- Integrate with different data source:
  - Replace nt_interface.py implementation but keep the same external methods used by tuner.py.

Safety & operational rules (explicit)
- Experiment-mode disable: if telemetry_interface.is_experiment_mode() indicates experiments must be disabled, tuner must not write coefficients.
- Clamping: enforce [min,max] from COEFFICIENT_TUNING for every write.
- Rate-limiting: enforce min_write_interval per-coefficient; configurable in tuner/config.py.
- Invalid data: define max_bad_samples; on exceed, pause tuning until sufficient good samples appear.
- Graceful shutdown: tuner.stop() flushes logs and closes telemetry connection.

State transitions (summary)
- IDLE --start--> TUNING_LOOP
- TUNING_LOOP --experiment_mode_on--> DISABLED
- TUNING_LOOP --invalid_data--> PAUSED
- PAUSED --good_data_restored--> TUNING_LOOP
- TUNING_LOOP --converged_current_coeff--> NEXT_COEFFICIENT or COMPLETE
- ANY --stop/exit--> SHUTDOWN

Testing strategy
- Unit tests must run offline and mock the telemetry interface:
  - Mock telemetry_interface.read_sample() to feed deterministic synthetic data.
  - Assert clamping: suggested values outside bounds are clamped before telemetry_interface.write_coefficient() is called.
  - Assert rate-limiting: repeated suggestions within the min interval do not trigger writes.
  - Optimizer tests: feed synthetic rewards and assert the optimizer model updates and converges.
- run_tests.py executes all unit tests (tuner/tests/*).

Debugging checklist
- Is telemetry connected? Check telemetry_interface logs and connection state.
- Is tuner disabled due to experiment-mode? telemetry_interface.is_experiment_mode()
- Are writes being throttled? Check timestamps in logs and min_write_interval.
- Is optimizer receiving results? Check logger entries for report_result events.
- Use DEBUG logging: setup_logging(config, log_level=logging.DEBUG)
