Place your three engine repositories here.

Expected directories:
- engines/phio
- engines/systemd-runner
- engines/sost

If you keep their original repo names, symlink them to these names.

The harness can run in two modes:
- Mock mode: tools/run_parallel.sh (works immediately, uses examples/)
- Real mode: tools/run_parallel_real.sh (requires repos here)

Autodetection (tools/engine_detect.py) looks for:
- PhiO: run_all_tests.sh (or scripts/run_all_tests.sh)
- SOST: scripts/run_sost.py
- Systemd-runner: a runner script (systemd_runner.py / runner.py etc.)

If your repos use other entrypoints, set explicit commands in config/engines.yaml
and adjust tools/run_parallel_real.sh accordingly.
