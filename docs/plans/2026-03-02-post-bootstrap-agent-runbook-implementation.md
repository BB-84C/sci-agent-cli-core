# Post-Bootstrap Agent Runbook Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `sci-cli-bootstrap` generate an agent-oriented README and `INTEGRATION_BRIEF.md` so bootstrapped projects can reach local runnable CLI delivery and optionally publish a GitHub release.

**Architecture:** Keep scaffold behavior centralized in `src/sci_agent_cli_core/scaffold.py` template renderers. Extend generated file map with a new integration brief template and replace generated README content with a deterministic runbook that supports unknown integration inputs and two release paths (`gh` + manual web upload).

**Tech Stack:** Python 3.10+, setuptools scaffold generator, pytest.

---

### Task 1: Add test coverage for new generated integration artifact

**Files:**
- Modify: `tests/test_scaffold.py`

**Step 1: Write the failing test assertion**

Add assertion in `test_scaffold_generates_driver_project` that generated project contains:

```python
assert (target / "INTEGRATION_BRIEF.md").exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_scaffold.py::test_scaffold_generates_driver_project -v`
Expected: FAIL because file does not yet exist.

**Step 3: Implement minimal code later (Task 2) to generate the file**

No code in this step.

**Step 4: Re-run test to verify it passes after Task 2**

Run: `pytest tests/test_scaffold.py::test_scaffold_generates_driver_project -v`
Expected: PASS.

### Task 2: Update scaffold templates for README runbook and integration brief

**Files:**
- Modify: `src/sci_agent_cli_core/scaffold.py`

**Step 1: Extend generated file list**

Add `INTEGRATION_BRIEF.md` entry to `files` dictionary in `main()`.

**Step 2: Add integration brief renderer**

Create `_render_integration_brief(...) -> str` returning a markdown template with:
- Required human intake items
- Integration mode selection
- Mapping table placeholders
- Safety/error/open-questions sections

**Step 3: Replace generated README renderer content**

Update `_render_driver_readme(...)` to include:
- Mission and hard constraints
- Human intake gate before coding
- Unknown-first discovery workflow
- Implementation boundary (`backend.py` vs `driver.py`)
- Verification (`pytest` + `sci-cli-conformance`)
- Build/install endpoint
- Release decision gate and dual release paths (`gh` and manual web)

**Step 4: Keep existing dynamic placeholders functional**

Ensure placeholders remain substituted for `project_name`, `package_name`, `cli_name`, example parameter/action names.

**Step 5: Run targeted scaffold tests**

Run: `pytest tests/test_scaffold.py -v`
Expected: PASS.

### Task 3: Verify no regressions across project tests

**Files:**
- Test: `tests/test_runtime.py`
- Test: `tests/test_conformance.py`
- Test: `tests/test_scaffold.py`

**Step 1: Run full suite**

Run: `pytest -v`
Expected: All tests pass.

**Step 2: Inspect generated output manually (optional smoke check)**

Run scaffold command in temp path and inspect that README and `INTEGRATION_BRIEF.md` are created.

### Task 4: Document and handoff

**Files:**
- Modify: none required unless follow-up docs are requested.

**Step 1: Summarize exact generated behavior changes**

Include file references and notable agent workflow gates.

**Step 2: Provide next-step options**

Offer commit/PR on request.
