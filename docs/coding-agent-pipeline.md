# Coding Agent Pipeline

This pipeline is for teams that want their coding agent to produce a strict
`nqctl`-style driver quickly.

## Outcome

You get a new CLI binary name (for example `laserctl`) that is wire-compatible
for:

- `capabilities`
- `get`
- `set`
- `ramp`
- `act`

You can add any extra commands after that.

## Step 1: Generate a driver scaffold

```powershell
sci-cli-bootstrap --output-dir D:\drivers\laserctl --cli-name laserctl --package-name laser_driver --project-name laser-instrument-driver
```

Generated project includes:

- `src/laser_driver/backend.py` (replace with real instrument calls)
- `src/laser_driver/driver.py` (core command mapping and payload shape)
- `src/laser_driver/cli.py` (runtime entrypoint)
- `tests/test_cli_contract.py` (smoke contract test)

## Step 2: Give your coding agent a focused task

Use this prompt as-is and replace placeholders:

```text
You are working in <driver-project-dir>.

Goal:
Hook real instrument Python control code into src/<package_name>/backend.py
while keeping strict wire compatibility for capabilities/get/set/ramp/act.

Rules:
1) Do not change output keys for the five core commands.
2) Keep error responses in nqctl style JSON envelope.
3) You may add extra commands, but do not break core commands.
4) Keep driver.py as the stable contract boundary; integrate hardware logic in backend.py.

Verification required:
- pytest
- sci-cli-conformance --command "<cli_name>" --get-parameter instrument_value --set-parameter instrument_value --set-arg Value=0.2 --ramp-parameter instrument_value --ramp-start 0.0 --ramp-end 0.4 --ramp-step 0.1 --action-name Instrument_Action --action-arg Mode=1
```

## Step 3: Validate locally

In the generated driver project:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
pytest
```

Run conformance:

```powershell
sci-cli-conformance --command "laserctl" --get-parameter instrument_value --set-parameter instrument_value --set-arg Value=0.2 --ramp-parameter instrument_value --ramp-start 0.0 --ramp-end 0.4 --ramp-step 0.1 --action-name Instrument_Action --action-arg Mode=1
```

## Step 4: Agent integration

In your instrument agent GUI/backend:

1. Let user enter CLI name (for example `laserctl`).
2. Call `<cli-name> capabilities` and register parameters/actions.
3. Keep using the same core calls (`cli_get`, `cli_set`, `cli_ramp`, `cli_action`).
