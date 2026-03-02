# Conformance Strict Schema Design

## Context

Current conformance checks validate command availability, exit behavior, error envelope, and required top-level keys, but do not strictly enforce full payload schema for all core commands.

## Goal

Enforce strict payload schema behavior for all five core commands in conformance checks:

- `capabilities`
- `get`
- `set`
- `ramp`
- `act`

## Chosen Approach

Implement strict built-in validators in `src/sci_agent_cli_core/conformance.py` (no external schema dependency).

## Why this approach

- Keeps the tool self-contained and dependency-free.
- Works consistently in constrained or offline environments.
- Avoids schema file loading and runtime version skew.

## Validation scope

### capabilities

- Top-level keys exactly: `parameters`, `action_commands`.
- Both sections must be objects with keys exactly `count`, `items`.
- `count` must be integer and match item array length.
- Parameter item keys exactly:
  `name`, `label`, `readable`, `writable`, `has_ramp`, `get_cmd`, `set_cmd`, `safety`.
- Action item keys exactly:
  `name`, `action_cmd`, `safety_mode`.
- Validate nested command field structure and primitive types.
- Validate action `safety_mode` enum (`alwaysAllowed`, `guarded`, `blocked`).

### get

- Exact keys: `parameter`, `value`, `fields`, `timestamp_utc`.
- `parameter` string, `fields` object, `timestamp_utc` string.

### set

- Exact keys: `parameter`, `plan_only`, `result`, `timestamp_utc`.
- `parameter` string, `plan_only` bool, `result` object, `timestamp_utc` string.

### ramp

- Exact keys:
  `parameter`, `start_value`, `end_value`, `step_value`, `interval_s`, `plan`, `applied`, `report`, `timestamp_utc`.
- Validate expected primitive/object types.

### act

- Exact keys: `action`, `plan_only`, `result`, `timestamp_utc`.
- `action` string, `plan_only` bool, `result` object, `timestamp_utc` string.

## Error reporting

- Keep existing `CheckResult` style and command-level failure reporting.
- Return specific schema mismatch reason for first detected violation.

## Testing strategy

- Add unit tests in `tests/test_conformance.py` for validators:
  - valid payload acceptance for each command.
  - invalid payload rejection for each command.
- Keep existing end-to-end demo conformance test.

## Risks and mitigations

- Risk: over-strict rules break older permissive payloads.
  - Mitigation: behavior is intentional for exact schema enforcement.
- Risk: verbose validator logic is harder to maintain.
  - Mitigation: use small reusable helpers for key/type checks.
