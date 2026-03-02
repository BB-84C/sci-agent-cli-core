# Conformance Strict Schema Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add exact schema enforcement for all five core command payloads in conformance checks.

**Architecture:** Keep validation logic in `src/sci_agent_cli_core/conformance.py` using small internal helper validators for key-set and type checks. Wire command checks to call strict validators after JSON parsing, and return precise mismatch reasons in `CheckResult` failures.

**Tech Stack:** Python 3.10+, pytest.

---

### Task 1: Add failing tests for strict schema behavior

**Files:**
- Modify: `tests/test_conformance.py`

**Step 1: Write failing tests for strict key/type validation**

Add tests that call new internal validator functions directly (to be implemented in Task 2), including:

- `capabilities` rejects extra parameter item keys.
- `capabilities` rejects invalid `safety_mode`.
- `get` rejects extra top-level keys.
- `set` rejects non-bool `plan_only`.
- `ramp` rejects non-object `plan`.
- `act` rejects non-object `result`.

Use representative payload snippets with minimal required fields.

**Step 2: Run target tests to confirm RED**

Run: `pytest tests/test_conformance.py -k strict_schema -v`
Expected: FAIL due to missing validator functions.

### Task 2: Implement strict validators in conformance checker

**Files:**
- Modify: `src/sci_agent_cli_core/conformance.py`

**Step 1: Add reusable validation helpers**

Implement helpers for:

- exact key set checks,
- object/list type checks,
- primitive type checks,
- optional object-or-null checks,
- deterministic error message formatting.

**Step 2: Add per-command strict validator functions**

Implement:

- `_validate_capabilities_payload(payload)`
- `_validate_get_payload(payload)`
- `_validate_set_payload(payload)`
- `_validate_ramp_payload(payload)`
- `_validate_act_payload(payload)`

Each returns `None` on success or error string on mismatch.

**Step 3: Wire validators into command checks**

Update `_check_capabilities`, `_check_get`, `_check_set`, `_check_ramp`, `_check_act` to call strict validators after parsing successful JSON object and exit-code checks.

**Step 4: Keep existing behavior**

Retain current command invocation flow and error envelope check behavior.

### Task 3: Turn tests GREEN and expand coverage

**Files:**
- Modify: `tests/test_conformance.py`

**Step 1: Update tests to target implemented validator APIs**

Ensure tests import and call validator functions from `sci_agent_cli_core.conformance`.

**Step 2: Add positive-path strict schema tests**

Add at least one valid payload case for each validator to ensure accepted shapes.

**Step 3: Run strict-schema subset**

Run: `pytest tests/test_conformance.py -k strict_schema -v`
Expected: PASS.

### Task 4: Full verification

**Files:**
- Test: `tests/test_conformance.py`
- Test: `tests/test_runtime.py`
- Test: `tests/test_scaffold.py`

**Step 1: Run conformance test module**

Run: `pytest tests/test_conformance.py -v`
Expected: PASS.

**Step 2: Run full suite**

Run: `pytest -v`
Expected: PASS.

### Task 5: Final reporting

**Files:**
- Modify: none required

**Step 1: Summarize exact schema guarantees now enforced**

List guaranteed constraints for all five commands and note where they live.

**Step 2: Suggest optional follow-up**

Optional: add external JSON schema document parity tests later.
