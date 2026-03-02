from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    details: str


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    base_command = shlex.split(args.command, posix=os.name != "nt")
    if not base_command:
        raise SystemExit("--command must not be empty")

    results: list[CheckResult] = []
    results.append(_check_capabilities(base_command))

    if args.get_parameter:
        results.append(_check_get(base_command, parameter=args.get_parameter))

    if args.set_parameter and (args.set_value or args.set_arg):
        results.append(
            _check_set(
                base_command,
                parameter=args.set_parameter,
                value=args.set_value,
                set_args=tuple(args.set_arg),
            )
        )

    if args.ramp_parameter:
        if args.ramp_start is None or args.ramp_end is None or args.ramp_step is None:
            results.append(
                CheckResult(
                    name="ramp",
                    ok=False,
                    details="Provide --ramp-start, --ramp-end, and --ramp-step with --ramp-parameter.",
                )
            )
        else:
            results.append(
                _check_ramp(
                    base_command,
                    parameter=args.ramp_parameter,
                    start=args.ramp_start,
                    end=args.ramp_end,
                    step=args.ramp_step,
                    interval_s=args.ramp_interval,
                )
            )

    if args.action_name:
        results.append(
            _check_act(
                base_command, action_name=args.action_name, action_args=tuple(args.action_arg)
            )
        )

    if not args.skip_error_check:
        results.append(
            _check_error_envelope(base_command, invalid_parameter=args.invalid_parameter)
        )

    _print_results(results=results, as_json=bool(args.json))
    return 0 if all(item.ok for item in results) else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sci-cli-conformance",
        description="Validate strict nqctl-core compatibility for an external CLI.",
    )
    parser.add_argument(
        "--command",
        required=True,
        help="Target command, for example: 'nqctl' or 'python examples/minimal_demo_driver.py'",
    )
    parser.add_argument("--json", action="store_true", help="Emit conformance report as JSON.")

    parser.add_argument("--get-parameter", help="Sample parameter for get checks.")

    parser.add_argument("--set-parameter", help="Sample parameter for set checks.")
    parser.add_argument("--set-value", help="Optional positional value for set checks.")
    parser.add_argument(
        "--set-arg",
        action="append",
        default=[],
        help="Repeatable set argument key=value for set checks.",
    )

    parser.add_argument("--ramp-parameter", help="Sample parameter for ramp checks.")
    parser.add_argument("--ramp-start", type=float)
    parser.add_argument("--ramp-end", type=float)
    parser.add_argument("--ramp-step", type=float)
    parser.add_argument("--ramp-interval", type=float, default=0.1)

    parser.add_argument("--action-name", help="Sample action name for act checks.")
    parser.add_argument(
        "--action-arg",
        action="append",
        default=[],
        help="Repeatable action arg key=value for act checks.",
    )

    parser.add_argument(
        "--invalid-parameter",
        default="__sci_agent_cli_core_invalid_parameter__",
        help="Parameter used for negative error-envelope check.",
    )
    parser.add_argument(
        "--skip-error-check",
        action="store_true",
        help="Skip JSON error-envelope validation call.",
    )
    return parser


def _check_capabilities(base_command: list[str]) -> CheckResult:
    code, payload, raw = _run_json(base_command, ["capabilities"])
    if code != 0:
        return CheckResult("capabilities", False, f"Expected exit 0, got {code}. Output: {raw}")
    if not isinstance(payload, dict):
        return CheckResult("capabilities", False, "Output is not JSON object.")
    if set(payload.keys()) != {"parameters", "action_commands"}:
        return CheckResult(
            "capabilities",
            False,
            "Top-level keys must be exactly {'parameters', 'action_commands'}.",
        )
    for key in ("parameters", "action_commands"):
        section = payload.get(key)
        if not isinstance(section, dict):
            return CheckResult("capabilities", False, f"'{key}' must be an object.")
        if "count" not in section or "items" not in section:
            return CheckResult("capabilities", False, f"'{key}' must contain 'count' and 'items'.")
    return CheckResult("capabilities", True, "ok")


def _check_get(base_command: list[str], *, parameter: str) -> CheckResult:
    code, payload, raw = _run_json(base_command, ["get", parameter])
    required = {"parameter", "value", "fields", "timestamp_utc"}
    return _check_success_payload("get", code, payload, raw, required_keys=required)


def _check_set(
    base_command: list[str],
    *,
    parameter: str,
    value: str | None,
    set_args: tuple[str, ...],
) -> CheckResult:
    command = ["set", parameter]
    if value is not None:
        command.append(value)
    for item in set_args:
        command.extend(["--arg", item])
    command.append("--plan-only")
    code, payload, raw = _run_json(base_command, command)
    required = {"parameter", "plan_only", "result", "timestamp_utc"}
    return _check_success_payload("set", code, payload, raw, required_keys=required)


def _check_ramp(
    base_command: list[str],
    *,
    parameter: str,
    start: float,
    end: float,
    step: float,
    interval_s: float,
) -> CheckResult:
    command = [
        "ramp",
        parameter,
        str(start),
        str(end),
        str(step),
        "--interval-s",
        str(interval_s),
        "--plan-only",
    ]
    code, payload, raw = _run_json(base_command, command)
    required = {
        "parameter",
        "start_value",
        "end_value",
        "step_value",
        "interval_s",
        "plan",
        "applied",
        "report",
        "timestamp_utc",
    }
    return _check_success_payload("ramp", code, payload, raw, required_keys=required)


def _check_act(
    base_command: list[str], *, action_name: str, action_args: tuple[str, ...]
) -> CheckResult:
    command = ["act", action_name]
    for item in action_args:
        command.extend(["--arg", item])
    command.append("--plan-only")
    code, payload, raw = _run_json(base_command, command)
    required = {"action", "plan_only", "result", "timestamp_utc"}
    return _check_success_payload("act", code, payload, raw, required_keys=required)


def _check_error_envelope(base_command: list[str], *, invalid_parameter: str) -> CheckResult:
    code, payload, raw = _run_json(base_command, ["get", invalid_parameter])
    if code == 0:
        return CheckResult("error_envelope", False, "Negative check unexpectedly returned exit 0.")
    if not isinstance(payload, dict):
        return CheckResult("error_envelope", False, f"Output is not JSON object: {raw}")
    if set(payload.keys()) != {"ok", "error", "exit_code"}:
        return CheckResult(
            "error_envelope", False, "Error payload keys must be {ok, error, exit_code}."
        )
    if payload.get("ok") is not False:
        return CheckResult("error_envelope", False, "Error payload field 'ok' must be false.")
    error_obj = payload.get("error")
    if not isinstance(error_obj, dict):
        return CheckResult("error_envelope", False, "Error payload field 'error' must be object.")
    if "type" not in error_obj or "message" not in error_obj:
        return CheckResult("error_envelope", False, "Error object must include type and message.")
    if payload.get("exit_code") != code:
        return CheckResult(
            "error_envelope", False, "Payload exit_code must equal process exit code."
        )
    return CheckResult("error_envelope", True, "ok")


def _check_success_payload(
    name: str,
    code: int,
    payload: dict[str, Any] | None,
    raw: str,
    *,
    required_keys: set[str],
) -> CheckResult:
    if code != 0:
        return CheckResult(name, False, f"Expected exit 0, got {code}. Output: {raw}")
    if not isinstance(payload, dict):
        return CheckResult(name, False, "Output is not JSON object.")
    missing = sorted(required_keys.difference(payload.keys()))
    if missing:
        return CheckResult(name, False, f"Missing required keys: {', '.join(missing)}")
    return CheckResult(name, True, "ok")


def _run_json(base_command: list[str], extra: list[str]) -> tuple[int, dict[str, Any] | None, str]:
    command = [*base_command, *extra, "--json"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    merged = stdout if stdout else stderr
    payload: dict[str, Any] | None = None
    if merged:
        try:
            parsed = json.loads(merged)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = None
    return completed.returncode, payload, merged


def _print_results(*, results: list[CheckResult], as_json: bool) -> None:
    if as_json:
        payload = {
            "ok": all(item.ok for item in results),
            "checks": [asdict(item) for item in results],
        }
        print(json.dumps(payload, indent=2))
        return

    for item in results:
        status = "PASS" if item.ok else "FAIL"
        print(f"[{status}] {item.name}: {item.details}")


if __name__ == "__main__":
    raise SystemExit(main())
