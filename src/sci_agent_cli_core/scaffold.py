from __future__ import annotations

import argparse
import re
from pathlib import Path
from textwrap import dedent


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir).expanduser().resolve()
    cli_name = _normalize_cli_name(args.cli_name)
    package_name = _normalize_package_name(args.package_name or f"{cli_name}_driver")
    project_name = str(args.project_name).strip() if args.project_name else output_dir.name

    parameter_name = "instrument_value"
    set_field_name = "Value"
    action_name = "Instrument_Action"
    action_arg_name = "Mode"

    files: dict[Path, str] = {
        output_dir / ".gitignore": _render_gitignore(),
        output_dir / "pyproject.toml": _render_pyproject(
            project_name=project_name,
            package_name=package_name,
            cli_name=cli_name,
        ),
        output_dir / "README.md": _render_driver_readme(
            project_name=project_name,
            package_name=package_name,
            cli_name=cli_name,
            parameter_name=parameter_name,
            set_field_name=set_field_name,
            action_name=action_name,
            action_arg_name=action_arg_name,
        ),
        output_dir / "INTEGRATION_BRIEF.md": _render_integration_brief(
            project_name=project_name,
            package_name=package_name,
            cli_name=cli_name,
            parameter_name=parameter_name,
            set_field_name=set_field_name,
            action_name=action_name,
            action_arg_name=action_arg_name,
        ),
        output_dir / "src" / package_name / "__init__.py": _render_init(),
        output_dir / "src" / package_name / "backend.py": _render_backend(
            parameter_name=parameter_name,
            set_field_name=set_field_name,
            action_name=action_name,
            action_arg_name=action_arg_name,
        ),
        output_dir / "src" / package_name / "driver.py": _render_driver(
            parameter_name=parameter_name,
            set_field_name=set_field_name,
            action_name=action_name,
            action_arg_name=action_arg_name,
        ),
        output_dir / "src" / package_name / "cli.py": _render_cli(
            package_name=package_name,
            cli_name=cli_name,
        ),
        output_dir / "tests" / "test_cli_contract.py": _render_driver_tests(
            package_name=package_name,
        ),
    }

    _ensure_target_ready(output_dir=output_dir, force=bool(args.force))
    for file_path, content in files.items():
        _write_file(file_path, content=content, force=bool(args.force))

    print(f"Created driver scaffold at {output_dir}")
    print(f"CLI name: {cli_name}")
    print(f"Package name: {package_name}")
    print("Next step: replace backend methods in src/<package>/backend.py with instrument calls.")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sci-cli-bootstrap",
        description="Generate a ready-to-hook instrument CLI driver project scaffold.",
    )
    parser.add_argument("--output-dir", required=True, help="Target directory for the new driver.")
    parser.add_argument(
        "--cli-name", required=True, help="Console command name, for example: laserctl"
    )
    parser.add_argument("--package-name", help="Python package name, defaults to <cli-name>_driver")
    parser.add_argument(
        "--project-name", help="Distribution/project name, defaults to output dir name"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files when output directory is not empty.",
    )
    return parser


def _normalize_cli_name(raw: str) -> str:
    candidate = str(raw).strip()
    if not candidate:
        raise ValueError("--cli-name cannot be empty.")
    if " " in candidate:
        raise ValueError("--cli-name must not contain spaces.")
    return candidate


def _normalize_package_name(raw: str) -> str:
    candidate = re.sub(r"[^a-zA-Z0-9_]", "_", str(raw).strip().lower())
    candidate = re.sub(r"_+", "_", candidate).strip("_")
    if not candidate:
        candidate = "instrument_driver"
    if candidate[0].isdigit():
        candidate = f"driver_{candidate}"
    return candidate


def _ensure_target_ready(*, output_dir: Path, force: bool) -> None:
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        return
    if not output_dir.is_dir():
        raise ValueError(f"Output path exists and is not a directory: {output_dir}")

    has_entries = any(output_dir.iterdir())
    if has_entries and not force:
        raise ValueError(
            f"Output directory is not empty: {output_dir}. Use --force to overwrite existing files."
        )


def _write_file(file_path: Path, *, content: str, force: bool) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.exists() and not force:
        raise ValueError(f"File already exists: {file_path}. Use --force to overwrite.")
    file_path.write_text(content, encoding="utf-8")


def _render_gitignore() -> str:
    return dedent(
        """\
        __pycache__/
        *.py[cod]
        .pytest_cache/
        .mypy_cache/
        .ruff_cache/
        .coverage
        build/
        dist/
        *.egg-info/
        .venv/
        """
    )


def _render_pyproject(*, project_name: str, package_name: str, cli_name: str) -> str:
    return dedent(
        f"""\
        [build-system]
        requires = ["setuptools>=69.0", "wheel"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "{project_name}"
        version = "0.1.0"
        description = "Instrument CLI driver built on sci-agent-cli-core"
        readme = "README.md"
        requires-python = ">=3.10"
        dependencies = [
            "sci-agent-cli-core>=0.1.0",
        ]

        [project.optional-dependencies]
        dev = [
            "pytest>=8.3.0",
            "ruff>=0.6.0",
            "black>=24.8.0",
            "mypy>=1.11.0",
        ]

        [project.scripts]
        {cli_name} = "{package_name}.cli:main"

        [tool.setuptools]
        package-dir = {{"" = "src"}}

        [tool.setuptools.packages.find]
        where = ["src"]
        include = ["{package_name}*"]

        [tool.pytest.ini_options]
        testpaths = ["tests"]
        """
    )


def _render_driver_readme(
    *,
    project_name: str,
    package_name: str,
    cli_name: str,
    parameter_name: str,
    set_field_name: str,
    action_name: str,
    action_arg_name: str,
) -> str:
    return dedent(
        f"""\
        # {project_name}

        Agent-oriented integration runbook for `sci-agent-cli-core` drivers.

        Command examples below use PowerShell syntax; adapt as needed for POSIX shells (bash/zsh).

        ## 1) Mission and hard constraints

        Mission: deliver a production-usable CLI integration while preserving the stable command contract.

        Hard constraints:

        - Keep wire-compatible CLI methods: `capabilities`, `get`, `set`, `ramp`, `act`.
        - Preserve JSON response shape semantics expected by conformance checks.
        - Treat unknown integration requirements as unresolved until clarified by a human.

        ## 2) Required human intake before coding

        Do not implement integration code until a human has completed `INTEGRATION_BRIEF.md`.

        Required intake artifacts (unknown-first, include what exists):

        - Documentation/specs (`.md`, `.pdf`, wiki exports).
        - SDKs or language bindings.
        - CSV/XLSX mappings.
        - Vendor tools/executables (`.exe`) and usage notes.
        - Archive drops (`.zip`) and extracted folder layout.
        - Raw folders with assets/scripts.
        - Example requests/responses, logs, or captures.

        ## 3) Discovery + mapping workflow

        1. Collect artifacts and record source + version.
        2. Identify parameter read/write surfaces and action surfaces.
        3. Map vendor names/types to CLI parameter/action schema.
        4. Document assumptions, unknowns, and risk items before coding.
        5. Implement one minimal end-to-end parameter and action path.
        6. Expand only after verification is green.

        ## 4) Implementation boundary

        - `src/{package_name}/backend.py`: flexible integration layer (protocol/SDK/device details).
        - `src/{package_name}/driver.py`: stable contract boundary (CLI semantics and payload shape).

        Keep placeholder defaults dynamic until replaced with verified mappings:

        - Parameter: `{parameter_name}` using field `{set_field_name}`
        - Action: `{action_name}` using arg `{action_arg_name}`

        ## 5) Verification commands

        Run both layers before any release decision:

        ```powershell
        python -m venv .venv
        .\\.venv\\Scripts\\Activate.ps1
        python -m pip install --upgrade pip
        python -m pip install -e .[dev]
        pytest
        ```

        ```powershell
        sci-cli-conformance --command "{cli_name}" --get-parameter {parameter_name} --set-parameter {parameter_name} --set-arg {set_field_name}=0.2 --ramp-parameter {parameter_name} --ramp-start 0.0 --ramp-end 0.4 --ramp-step 0.1 --action-name {action_name} --action-arg {action_arg_name}=1
        ```

        ## 6) Local build/install endpoint

        ```powershell
        python -m build
        python -m pip install --force-reinstall dist\\*.whl
        {cli_name} capabilities --json
        ```

        ## 7) Release decision gate (human required)

        Stop after local verification and require explicit human approval before running any publish/release command.

        Use a policy gate: no approval, no release.

        ## 8) Release paths

        ### Path A: GitHub CLI

        Replace placeholders before running:

        - `<RELEASE_TAG>` (for example: `v0.1.0`)
        - `<REMOTE_NAME>` (for example: `origin`)

        ```powershell
        git tag <RELEASE_TAG>
        git push <REMOTE_NAME> <RELEASE_TAG>
        gh release create <RELEASE_TAG> dist/* --title "<RELEASE_TAG>" --notes "Release for {project_name}."
        ```

        ### Path B: Manual GitHub web upload

        1. Replace `<RELEASE_TAG>` and `<REMOTE_NAME>` with your values.
        2. Create and push tag `<RELEASE_TAG>`.
        3. Open repository Releases page.
        4. Draft release for `<RELEASE_TAG>`.
        5. Upload artifacts from `dist/`.
        6. Publish after human review.
        """
    )


def _render_integration_brief(
    *,
    project_name: str,
    package_name: str,
    cli_name: str,
    parameter_name: str,
    set_field_name: str,
    action_name: str,
    action_arg_name: str,
) -> str:
    return dedent(
        f"""\
        # Integration Brief - {project_name}

        Complete this brief with a human partner before integration coding starts.

        ## Project context

        - Project: `{project_name}`
        - Package: `{package_name}`
        - CLI: `{cli_name}`

        ## Required human intake

        Capture all known inputs and source locations:

        - Docs/specs (`.md`, `.pdf`, wiki exports):
        - SDK/API package(s):
        - CSV mapping files:
        - XLSX mapping files:
        - Executables (`.exe`) and invocation notes:
        - ZIP bundles (`.zip`) and extraction notes:
        - Folder-based assets/scripts:
        - Sample requests/responses/logs:

        ## Integration mode selection

        - Primary mode: [ ] Native SDK [ ] Process/CLI [ ] Serial [ ] TCP [ ] Other:
        - Transport details (host/port/device path/baud):
        - Auth/secrets needed:
        - Platform/runtime constraints:

        ## Discovery + mapping table

        | Surface | Vendor Name | Driver Name | Args/Fields | Type/Units | Notes |
        | --- | --- | --- | --- | --- | --- |
        | Parameter | TBD | {parameter_name} | {set_field_name} | TBD | |
        | Action | TBD | {action_name} | {action_arg_name} | TBD | |

        ## Safety constraints

        - Allowed ranges and limits:
        - Ramp/step limits:
        - Interlocks/guardrails:
        - Operator confirmation requirements:

        ## Error handling expectations

        - Vendor error codes/messages:
        - Timeout + retry policy:
        - Recoverable vs fatal failures:
        - Logging/audit expectations:

        ## Open questions

        -
        -
        -
        """
    )


def _render_init() -> str:
    return dedent(
        """\
        __version__ = "0.1.0"
        """
    )


def _render_backend(
    *,
    parameter_name: str,
    set_field_name: str,
    action_name: str,
    action_arg_name: str,
) -> str:
    return dedent(
        f"""\
        from __future__ import annotations

        from typing import Any


        class InstrumentBackend:
            def __init__(self) -> None:
                self._value = 0.0
                self._mode = 0

            def read_parameter(self, parameter: str) -> dict[str, Any]:
                if parameter != "{parameter_name}":
                    raise ValueError(f"Unknown parameter: {{parameter}}")
                return {{"{set_field_name}": self._value}}

            def write_parameter(
                self,
                parameter: str,
                *,
                target_value: float,
                interval_s: float | None,
                plan_only: bool,
            ) -> dict[str, Any]:
                if parameter != "{parameter_name}":
                    raise ValueError(f"Unknown parameter: {{parameter}}")
                if not plan_only:
                    self._value = float(target_value)
                return {{
                    "accepted": True,
                    "target": float(target_value),
                    "interval_s": interval_s,
                    "plan_only": bool(plan_only),
                }}

            def ramp_parameter(
                self,
                parameter: str,
                *,
                start: float,
                end: float,
                step: float,
                interval_s: float,
                plan_only: bool,
            ) -> dict[str, Any]:
                if parameter != "{parameter_name}":
                    raise ValueError(f"Unknown parameter: {{parameter}}")

                direction = 1.0 if end >= start else -1.0
                step_value = abs(step)
                points = [float(start)]
                current = float(start)
                while True:
                    next_value = current + direction * step_value
                    if (direction > 0 and next_value >= end) or (direction < 0 and next_value <= end):
                        break
                    points.append(float(next_value))
                    current = next_value
                points.append(float(end))

                if not plan_only:
                    self._value = float(end)

                return {{
                    "plan": {{"steps": points, "count": len(points), "interval_s": interval_s}},
                    "applied": not plan_only,
                    "report": None if plan_only else {{"steps_applied": len(points), "dry_run": False}},
                }}

            def execute_action(
                self,
                action_name: str,
                *,
                args: dict[str, str],
                plan_only: bool,
            ) -> dict[str, Any]:
                if action_name != "{action_name}":
                    raise ValueError(f"Unknown action: {{action_name}}")

                mode_raw = args.get("{action_arg_name}", "0")
                mode_value = int(mode_raw)
                if not plan_only:
                    self._mode = mode_value

                return {{
                    "accepted": True,
                    "mode": mode_value,
                    "plan_only": bool(plan_only),
                }}
        """
    )


def _render_driver(
    *,
    parameter_name: str,
    set_field_name: str,
    action_name: str,
    action_arg_name: str,
) -> str:
    return dedent(
        f"""\
        from __future__ import annotations

        from datetime import datetime, timezone
        from typing import Any

        from sci_agent_cli_core.driver import BaseInstrumentCliDriver
        from sci_agent_cli_core.errors import InvalidInputError

        from .backend import InstrumentBackend


        def _now_utc_iso() -> str:
            return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


        class InstrumentDriver(BaseInstrumentCliDriver):
            def __init__(self, backend: InstrumentBackend | None = None) -> None:
                self._backend = backend or InstrumentBackend()

            def capabilities(
                self,
                *,
                include_backend_commands: bool = False,
                backend_match: str | None = None,
            ) -> dict[str, Any]:
                del include_backend_commands
                del backend_match
                return {{
                    "parameters": {{
                        "count": 1,
                        "items": [
                            {{
                                "name": "{parameter_name}",
                                "label": "Instrument Value",
                                "readable": True,
                                "writable": True,
                                "has_ramp": True,
                                "get_cmd": {{
                                    "command": "Instrument.ValueGet",
                                    "payload_index": 0,
                                    "arg_fields": [],
                                    "response_fields": [
                                        {{
                                            "index": 0,
                                            "name": "{set_field_name}",
                                            "type": "float",
                                            "unit": "",
                                            "wire_type": "f",
                                            "description": "Instrument value",
                                        }}
                                    ],
                                }},
                                "set_cmd": {{
                                    "command": "Instrument.ValueSet",
                                    "arg_fields": [
                                        {{
                                            "name": "{set_field_name}",
                                            "type": "float",
                                            "unit": "",
                                            "wire_type": "f",
                                            "required": True,
                                            "description": "Target value",
                                            "default": None,
                                        }}
                                    ],
                                }},
                                "safety": {{
                                    "min_value": None,
                                    "max_value": None,
                                    "max_step": None,
                                    "max_slew_per_s": None,
                                    "cooldown_s": None,
                                    "ramp_enabled": True,
                                    "ramp_interval_s": 0.1,
                                }},
                            }}
                        ],
                    }},
                    "action_commands": {{
                        "count": 1,
                        "items": [
                            {{
                                "name": "{action_name}",
                                "action_cmd": {{
                                    "command": "Instrument.Action",
                                    "arg_fields": [
                                        {{
                                            "name": "{action_arg_name}",
                                            "type": "int",
                                            "unit": "",
                                            "wire_type": "i",
                                            "required": False,
                                            "description": "Action mode",
                                            "default": 0,
                                        }}
                                    ],
                                }},
                                "safety_mode": "guarded",
                            }}
                        ],
                    }},
                }}

            def get(self, parameter: str) -> dict[str, Any]:
                try:
                    fields = self._backend.read_parameter(parameter)
                except ValueError as exc:
                    raise InvalidInputError(str(exc)) from exc
                value = next(iter(fields.values())) if len(fields) == 1 else fields
                return {{
                    "parameter": parameter,
                    "value": value,
                    "fields": fields,
                    "timestamp_utc": _now_utc_iso(),
                }}

            def set(
                self,
                parameter: str,
                *,
                value: str | None,
                args: dict[str, str],
                interval_s: float | None,
                plan_only: bool,
            ) -> dict[str, Any]:
                target_raw = value if value is not None else args.get("{set_field_name}")
                if target_raw is None:
                    raise InvalidInputError(
                        "Missing set target. Use positional <value> or --arg {set_field_name}=<value>."
                    )
                try:
                    target_value = float(target_raw)
                    result = self._backend.write_parameter(
                        parameter,
                        target_value=target_value,
                        interval_s=interval_s,
                        plan_only=plan_only,
                    )
                except ValueError as exc:
                    raise InvalidInputError(str(exc)) from exc
                return {{
                    "parameter": parameter,
                    "plan_only": bool(plan_only),
                    "result": result,
                    "timestamp_utc": _now_utc_iso(),
                }}

            def ramp(
                self,
                parameter: str,
                *,
                start: float,
                end: float,
                step: float,
                interval_s: float,
                plan_only: bool,
            ) -> dict[str, Any]:
                try:
                    ramp_payload = self._backend.ramp_parameter(
                        parameter,
                        start=start,
                        end=end,
                        step=step,
                        interval_s=interval_s,
                        plan_only=plan_only,
                    )
                except ValueError as exc:
                    raise InvalidInputError(str(exc)) from exc
                return {{
                    "parameter": parameter,
                    "start_value": start,
                    "end_value": end,
                    "step_value": step,
                    "interval_s": interval_s,
                    "plan": ramp_payload["plan"],
                    "applied": ramp_payload["applied"],
                    "report": ramp_payload["report"],
                    "timestamp_utc": _now_utc_iso(),
                }}

            def act(self, action_name: str, *, args: dict[str, str], plan_only: bool) -> dict[str, Any]:
                try:
                    result = self._backend.execute_action(action_name, args=args, plan_only=plan_only)
                except ValueError as exc:
                    raise InvalidInputError(str(exc)) from exc
                return {{
                    "action": action_name,
                    "plan_only": bool(plan_only),
                    "result": result,
                    "timestamp_utc": _now_utc_iso(),
                }}
        """
    )


def _render_cli(*, package_name: str, cli_name: str) -> str:
    return dedent(
        f"""\
        from __future__ import annotations

        from collections.abc import Sequence

        from sci_agent_cli_core.runtime import run_cli

        from {package_name}.driver import InstrumentDriver


        def main(argv: Sequence[str] | None = None) -> int:
            return run_cli(InstrumentDriver(), argv=argv, prog="{cli_name}")


        if __name__ == "__main__":
            raise SystemExit(main())
        """
    )


def _render_driver_tests(*, package_name: str) -> str:
    return dedent(
        f"""\
        from __future__ import annotations

        import json

        from {package_name}.cli import main


        def test_capabilities_smoke(capsys) -> None:
            exit_code = main(["capabilities", "--json"])
            assert exit_code == 0
            payload = json.loads(capsys.readouterr().out)
            assert set(payload.keys()) == {{"parameters", "action_commands"}}
        """
    )
