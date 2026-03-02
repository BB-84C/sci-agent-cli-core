# sci-agent-cli-core

Reusable Python framework for instrument CLIs that must be wire-compatible with the
`nqctl` core contract.

## Scope

This project standardizes exactly five commands:

- `capabilities`
- `get`
- `set`
- `ramp`
- `act`

Drivers can keep any executable name (`nqctl`, `laserctl`, `scopectl`, etc.), but
the command behavior, JSON payloads, and exit codes for the five core commands must
match the contract.

## What is included

- `sci_agent_cli_core.runtime`: shared argparse runtime with strict error envelope.
- `sci_agent_cli_core.driver`: abstract driver interface for the five core operations.
- `sci_agent_cli_core.conformance`: CLI compatibility checks for external drivers.
- `docs/contract-v1.md`: frozen `core-v1` contract reference.
- `examples/minimal_demo_driver.py`: starter implementation template.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
pytest
```

Run the demo driver:

```powershell
python examples/minimal_demo_driver.py capabilities
python examples/minimal_demo_driver.py get bias_v
```

Run conformance against the demo:

```powershell
sci-cli-conformance --command "python examples/minimal_demo_driver.py" --get-parameter bias_v --set-parameter bias_v --set-arg Bias_value_V=0.1 --ramp-parameter bias_v --ramp-start 0.0 --ramp-end 0.2 --ramp-step 0.05 --action-name Scan_Action --action-arg Scan_action=0
```
