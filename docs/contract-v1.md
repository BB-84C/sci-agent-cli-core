# SCI Agent CLI Core Contract v1

## Required commands

Every compliant driver must expose these commands with nqctl-compatible behavior:

- `capabilities`
- `get <parameter>`
- `set <parameter> [<value>] [--arg key=value ...] [--interval-s <sec>] [--plan-only]`
- `ramp <parameter> <start> <end> <step> --interval-s <sec> [--plan-only]`
- `act <action_name> [--arg key=value ...] [--plan-only]`

JSON output is default. `--text` can be supported for human readability.

## Exit codes

- `0`: success
- `1`: generic failure
- `2`: policy blocked
- `3`: invalid input / protocol-shape issue
- `4`: unavailable command/backend capability
- `5`: connection/timeout failure

## Error envelope (strict)

For command failures in JSON mode, payload must be:

```json
{
  "ok": false,
  "error": {
    "type": "ErrorTypeName",
    "message": "Human readable message"
  },
  "exit_code": 3
}
```

`exit_code` in payload must match process return code.

## Core payload requirements

`capabilities` must return exactly top-level keys:

- `parameters` (`count`, `items`)
- `action_commands` (`count`, `items`)

`get` required keys:

- `parameter`, `value`, `fields`, `timestamp_utc`

`set` required keys:

- `parameter`, `plan_only`, `result`, `timestamp_utc`

`ramp` required keys:

- `parameter`, `start_value`, `end_value`, `step_value`, `interval_s`, `plan`, `applied`, `report`, `timestamp_utc`

`act` required keys:

- `action`, `plan_only`, `result`, `timestamp_utc`

Optional keys are allowed only where nqctl may emit them (for example trajectory stats).
