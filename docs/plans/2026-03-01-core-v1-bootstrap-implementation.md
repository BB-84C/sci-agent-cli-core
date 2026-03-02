# SCI Agent CLI Core v1 Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Bootstrap an independent `sci-agent-cli-core` project that provides a strict nqctl-core-compatible runtime and conformance checker.

**Architecture:** Keep the project Python-only and dependency-light. Put reusable runtime logic in `src/sci_agent_cli_core/runtime.py`, define a small driver ABC in `driver.py`, and add a standalone conformance command in `conformance.py` for third-party CLI validation.

**Tech Stack:** Python 3.10+, argparse, subprocess, pytest, setuptools

---

### Task 1: Create package scaffold and metadata

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`

**Step 1: Write the failing test**

```python
def test_package_imports():
    import sci_agent_cli_core
    assert sci_agent_cli_core.__version__
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_runtime.py::test_package_imports -v`
Expected: FAIL due to missing package files

**Step 3: Write minimal implementation**

- Add package metadata and editable-install support from `src/`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_runtime.py::test_package_imports -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml .gitignore README.md
git commit -m "chore: bootstrap sci-agent-cli-core packaging"
```

### Task 2: Implement contract constants and error model

**Files:**
- Create: `src/sci_agent_cli_core/contracts.py`
- Create: `src/sci_agent_cli_core/errors.py`
- Test: `tests/test_runtime.py`

**Step 1: Write the failing test**

```python
def test_error_payload_shape():
    payload = build_error_payload(exit_code=3, error_type="ValueError", message="bad input")
    assert payload["ok"] is False
    assert payload["exit_code"] == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_runtime.py::test_error_payload_shape -v`
Expected: FAIL with import/name error

**Step 3: Write minimal implementation**

- Define exit-code constants and strict JSON error helper.
- Define `CliCoreError` subclasses for policy/input/connection/unavailable flows.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_runtime.py::test_error_payload_shape -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/sci_agent_cli_core/contracts.py src/sci_agent_cli_core/errors.py tests/test_runtime.py
git commit -m "feat: add core contract constants and error types"
```

### Task 3: Implement shared runtime and parser

**Files:**
- Create: `src/sci_agent_cli_core/driver.py`
- Create: `src/sci_agent_cli_core/runtime.py`
- Modify: `tests/test_runtime.py`

**Step 1: Write the failing test**

```python
def test_runtime_capabilities_command(capsys):
    code = run_cli(FakeDriver(), ["capabilities", "--json"], prog="democtl")
    assert code == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_runtime.py::test_runtime_capabilities_command -v`
Expected: FAIL because `run_cli` is missing

**Step 3: Write minimal implementation**

- Add command parsing/dispatch for `capabilities/get/set/ramp/act`.
- Add `--arg key=value` parsing with duplicate-key rejection.
- Add nqctl-style JSON error envelope + exit code handling.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_runtime.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/sci_agent_cli_core/driver.py src/sci_agent_cli_core/runtime.py tests/test_runtime.py
git commit -m "feat: add reusable nqctl-core runtime dispatcher"
```

### Task 4: Add conformance command and demo driver

**Files:**
- Create: `src/sci_agent_cli_core/conformance.py`
- Create: `examples/minimal_demo_driver.py`
- Create: `tests/test_conformance.py`

**Step 1: Write the failing test**

```python
def test_conformance_passes_for_demo_driver():
    assert main([...]) == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_conformance.py::test_conformance_passes_for_demo_driver -v`
Expected: FAIL due to missing conformance module

**Step 3: Write minimal implementation**

- Execute target CLI commands through subprocess.
- Validate payload keys and error envelope semantics.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_conformance.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/sci_agent_cli_core/conformance.py examples/minimal_demo_driver.py tests/test_conformance.py
git commit -m "feat: add cli conformance checker and demo driver"
```

### Task 5: Document the frozen core contract

**Files:**
- Create: `docs/contract-v1.md`

**Step 1: Write the failing test**

```python
def test_contract_doc_lists_core_commands():
    text = Path("docs/contract-v1.md").read_text(encoding="utf-8")
    assert "capabilities" in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_conformance.py::test_contract_doc_lists_core_commands -v`
Expected: FAIL because the doc does not exist

**Step 3: Write minimal implementation**

- Document required commands, payload keys, and exit codes.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_conformance.py::test_contract_doc_lists_core_commands -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/contract-v1.md
git commit -m "docs: publish core-v1 contract"
```
