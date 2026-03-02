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

    if args.set_parameter:
        if args.set_value is None and not args.set_arg:
            results.append(
                CheckResult(
                    name="set",
                    ok=False,
                    details="Provide --set-value or --set-arg with --set-parameter.",
                )
            )
        else:
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
    error = _validate_capabilities_payload(payload)
    if error is not None:
        return CheckResult("capabilities", False, error)
    return CheckResult("capabilities", True, "ok")


def _check_get(base_command: list[str], *, parameter: str) -> CheckResult:
    code, payload, raw = _run_json(base_command, ["get", parameter])
    if code != 0:
        return CheckResult("get", False, f"Expected exit 0, got {code}. Output: {raw}")
    if not isinstance(payload, dict):
        return CheckResult("get", False, "Output is not JSON object.")
    error = _validate_get_payload(payload)
    if error is not None:
        return CheckResult("get", False, error)
    return CheckResult("get", True, "ok")


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
    if code != 0:
        return CheckResult("set", False, f"Expected exit 0, got {code}. Output: {raw}")
    if not isinstance(payload, dict):
        return CheckResult("set", False, "Output is not JSON object.")
    error = _validate_set_payload(payload)
    if error is not None:
        return CheckResult("set", False, error)
    return CheckResult("set", True, "ok")


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
    if code != 0:
        return CheckResult("ramp", False, f"Expected exit 0, got {code}. Output: {raw}")
    if not isinstance(payload, dict):
        return CheckResult("ramp", False, "Output is not JSON object.")
    error = _validate_ramp_payload(payload)
    if error is not None:
        return CheckResult("ramp", False, error)
    return CheckResult("ramp", True, "ok")


def _check_act(
    base_command: list[str], *, action_name: str, action_args: tuple[str, ...]
) -> CheckResult:
    command = ["act", action_name]
    for item in action_args:
        command.extend(["--arg", item])
    command.append("--plan-only")
    code, payload, raw = _run_json(base_command, command)
    if code != 0:
        return CheckResult("act", False, f"Expected exit 0, got {code}. Output: {raw}")
    if not isinstance(payload, dict):
        return CheckResult("act", False, "Output is not JSON object.")
    error = _validate_act_payload(payload)
    if error is not None:
        return CheckResult("act", False, error)
    return CheckResult("act", True, "ok")


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


def _validate_capabilities_payload(payload: dict[str, Any]) -> str | None:
    error = _validate_exact_keys(
        payload, expected={"parameters", "action_commands"}, path="capabilities"
    )
    if error is not None:
        return error

    parameters = payload.get("parameters")
    actions = payload.get("action_commands")

    error = _validate_capability_section(parameters, path="capabilities.parameters")
    if error is not None:
        return error
    error = _validate_capability_section(actions, path="capabilities.action_commands")
    if error is not None:
        return error

    assert isinstance(parameters, dict)
    assert isinstance(actions, dict)

    parameter_items = parameters.get("items")
    action_items = actions.get("items")

    assert isinstance(parameter_items, list)
    assert isinstance(action_items, list)

    for index, item in enumerate(parameter_items):
        error = _validate_parameter_item(item, path=f"capabilities.parameters.items[{index}]")
        if error is not None:
            return error

    for index, item in enumerate(action_items):
        error = _validate_action_item(item, path=f"capabilities.action_commands.items[{index}]")
        if error is not None:
            return error

    return None


def _validate_get_payload(payload: dict[str, Any]) -> str | None:
    error = _validate_exact_keys(
        payload,
        expected={"parameter", "value", "fields", "timestamp_utc"},
        path="get",
    )
    if error is not None:
        return error
    error = _validate_string(payload.get("parameter"), path="get.parameter")
    if error is not None:
        return error
    error = _validate_object(payload.get("fields"), path="get.fields")
    if error is not None:
        return error
    return _validate_string(payload.get("timestamp_utc"), path="get.timestamp_utc")


def _validate_set_payload(payload: dict[str, Any]) -> str | None:
    error = _validate_exact_keys(
        payload,
        expected={"parameter", "plan_only", "result", "timestamp_utc"},
        path="set",
    )
    if error is not None:
        return error
    error = _validate_string(payload.get("parameter"), path="set.parameter")
    if error is not None:
        return error
    error = _validate_bool(payload.get("plan_only"), path="set.plan_only")
    if error is not None:
        return error
    error = _validate_object(payload.get("result"), path="set.result")
    if error is not None:
        return error
    return _validate_string(payload.get("timestamp_utc"), path="set.timestamp_utc")


def _validate_ramp_payload(payload: dict[str, Any]) -> str | None:
    error = _validate_exact_keys(
        payload,
        expected={
            "parameter",
            "start_value",
            "end_value",
            "step_value",
            "interval_s",
            "plan",
            "applied",
            "report",
            "timestamp_utc",
        },
        path="ramp",
    )
    if error is not None:
        return error

    checks = [
        _validate_string(payload.get("parameter"), path="ramp.parameter"),
        _validate_number(payload.get("start_value"), path="ramp.start_value"),
        _validate_number(payload.get("end_value"), path="ramp.end_value"),
        _validate_number(payload.get("step_value"), path="ramp.step_value"),
        _validate_number(payload.get("interval_s"), path="ramp.interval_s"),
        _validate_object(payload.get("plan"), path="ramp.plan"),
        _validate_bool(payload.get("applied"), path="ramp.applied"),
        _validate_object_or_null(payload.get("report"), path="ramp.report"),
        _validate_string(payload.get("timestamp_utc"), path="ramp.timestamp_utc"),
    ]
    for item in checks:
        if item is not None:
            return item
    return None


def _validate_act_payload(payload: dict[str, Any]) -> str | None:
    error = _validate_exact_keys(
        payload,
        expected={"action", "plan_only", "result", "timestamp_utc"},
        path="act",
    )
    if error is not None:
        return error
    error = _validate_string(payload.get("action"), path="act.action")
    if error is not None:
        return error
    error = _validate_bool(payload.get("plan_only"), path="act.plan_only")
    if error is not None:
        return error
    error = _validate_object(payload.get("result"), path="act.result")
    if error is not None:
        return error
    return _validate_string(payload.get("timestamp_utc"), path="act.timestamp_utc")


def _validate_capability_section(value: Any, *, path: str) -> str | None:
    error = _validate_object(value, path=path)
    if error is not None:
        return error
    assert isinstance(value, dict)
    error = _validate_exact_keys(value, expected={"count", "items"}, path=path)
    if error is not None:
        return error
    error = _validate_int(value.get("count"), path=f"{path}.count")
    if error is not None:
        return error
    error = _validate_list(value.get("items"), path=f"{path}.items")
    if error is not None:
        return error
    count = value.get("count")
    items = value.get("items")
    assert isinstance(count, int)
    assert isinstance(items, list)
    if count != len(items):
        return f"{path}.count must match len({path}.items)."
    return None


def _validate_parameter_item(value: Any, *, path: str) -> str | None:
    error = _validate_object(value, path=path)
    if error is not None:
        return error
    assert isinstance(value, dict)
    error = _validate_exact_keys(
        value,
        expected={
            "name",
            "label",
            "readable",
            "writable",
            "has_ramp",
            "get_cmd",
            "set_cmd",
            "safety",
        },
        path=path,
    )
    if error is not None:
        return error

    checks = [
        _validate_string(value.get("name"), path=f"{path}.name"),
        _validate_string(value.get("label"), path=f"{path}.label"),
        _validate_bool(value.get("readable"), path=f"{path}.readable"),
        _validate_bool(value.get("writable"), path=f"{path}.writable"),
        _validate_bool(value.get("has_ramp"), path=f"{path}.has_ramp"),
        _validate_command_descriptor(value.get("get_cmd"), path=f"{path}.get_cmd", kind="get"),
        _validate_command_descriptor(value.get("set_cmd"), path=f"{path}.set_cmd", kind="set"),
        _validate_safety_descriptor(value.get("safety"), path=f"{path}.safety"),
    ]
    for item in checks:
        if item is not None:
            return item
    return None


def _validate_action_item(value: Any, *, path: str) -> str | None:
    error = _validate_object(value, path=path)
    if error is not None:
        return error
    assert isinstance(value, dict)
    error = _validate_exact_keys(value, expected={"name", "action_cmd", "safety_mode"}, path=path)
    if error is not None:
        return error
    error = _validate_string(value.get("name"), path=f"{path}.name")
    if error is not None:
        return error
    error = _validate_command_descriptor(
        value.get("action_cmd"), path=f"{path}.action_cmd", kind="action"
    )
    if error is not None:
        return error

    safety_mode = value.get("safety_mode")
    error = _validate_string(safety_mode, path=f"{path}.safety_mode")
    if error is not None:
        return error
    assert isinstance(safety_mode, str)
    allowed = {"alwaysAllowed", "guarded", "blocked"}
    if safety_mode not in allowed:
        return f"{path}.safety_mode must be one of {_format_keys(allowed)}."
    return None


def _validate_command_descriptor(value: Any, *, path: str, kind: str) -> str | None:
    error = _validate_object(value, path=path)
    if error is not None:
        return error
    assert isinstance(value, dict)

    if kind == "get":
        required = {"command", "payload_index", "arg_fields", "response_fields"}
    else:
        required = {"command", "arg_fields"}
    error = _validate_required_with_optional_keys(
        value,
        required=required,
        optional={"description"},
        path=path,
    )
    if error is not None:
        return error

    error = _validate_string(value.get("command"), path=f"{path}.command")
    if error is not None:
        return error

    if kind == "get":
        error = _validate_int(value.get("payload_index"), path=f"{path}.payload_index")
        if error is not None:
            return error

    arg_fields = value.get("arg_fields")
    error = _validate_list(arg_fields, path=f"{path}.arg_fields")
    if error is not None:
        return error
    assert isinstance(arg_fields, list)
    for index, item in enumerate(arg_fields):
        error = _validate_arg_field_descriptor(item, path=f"{path}.arg_fields[{index}]")
        if error is not None:
            return error

    if kind == "get":
        response_fields = value.get("response_fields")
        error = _validate_list(response_fields, path=f"{path}.response_fields")
        if error is not None:
            return error
        assert isinstance(response_fields, list)
        for index, item in enumerate(response_fields):
            error = _validate_response_field_descriptor(
                item, path=f"{path}.response_fields[{index}]"
            )
            if error is not None:
                return error
    return None


def _validate_arg_field_descriptor(value: Any, *, path: str) -> str | None:
    error = _validate_object(value, path=path)
    if error is not None:
        return error
    assert isinstance(value, dict)
    error = _validate_exact_keys(
        value,
        expected={"name", "type", "unit", "wire_type", "required", "description", "default"},
        path=path,
    )
    if error is not None:
        return error

    checks = [
        _validate_string(value.get("name"), path=f"{path}.name"),
        _validate_string(value.get("type"), path=f"{path}.type"),
        _validate_string(value.get("unit"), path=f"{path}.unit"),
        _validate_string(value.get("wire_type"), path=f"{path}.wire_type"),
        _validate_bool(value.get("required"), path=f"{path}.required"),
        _validate_string(value.get("description"), path=f"{path}.description"),
    ]
    for item in checks:
        if item is not None:
            return item
    return None


def _validate_response_field_descriptor(value: Any, *, path: str) -> str | None:
    error = _validate_object(value, path=path)
    if error is not None:
        return error
    assert isinstance(value, dict)
    error = _validate_exact_keys(
        value,
        expected={"index", "name", "type", "unit", "wire_type", "description"},
        path=path,
    )
    if error is not None:
        return error

    checks = [
        _validate_int(value.get("index"), path=f"{path}.index"),
        _validate_string(value.get("name"), path=f"{path}.name"),
        _validate_string(value.get("type"), path=f"{path}.type"),
        _validate_string(value.get("unit"), path=f"{path}.unit"),
        _validate_string(value.get("wire_type"), path=f"{path}.wire_type"),
        _validate_string(value.get("description"), path=f"{path}.description"),
    ]
    for item in checks:
        if item is not None:
            return item
    return None


def _validate_safety_descriptor(value: Any, *, path: str) -> str | None:
    error = _validate_object(value, path=path)
    if error is not None:
        return error
    assert isinstance(value, dict)
    error = _validate_exact_keys(
        value,
        expected={
            "min_value",
            "max_value",
            "max_step",
            "max_slew_per_s",
            "cooldown_s",
            "ramp_enabled",
            "ramp_interval_s",
        },
        path=path,
    )
    if error is not None:
        return error

    checks = [
        _validate_number_or_null(value.get("min_value"), path=f"{path}.min_value"),
        _validate_number_or_null(value.get("max_value"), path=f"{path}.max_value"),
        _validate_number_or_null(value.get("max_step"), path=f"{path}.max_step"),
        _validate_number_or_null(value.get("max_slew_per_s"), path=f"{path}.max_slew_per_s"),
        _validate_number_or_null(value.get("cooldown_s"), path=f"{path}.cooldown_s"),
        _validate_bool(value.get("ramp_enabled"), path=f"{path}.ramp_enabled"),
        _validate_number_or_null(value.get("ramp_interval_s"), path=f"{path}.ramp_interval_s"),
    ]
    for item in checks:
        if item is not None:
            return item
    return None


def _validate_exact_keys(value: dict[str, Any], *, expected: set[str], path: str) -> str | None:
    actual = set(value.keys())
    if actual == expected:
        return None
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    parts: list[str] = []
    if missing:
        parts.append(f"missing {missing}")
    if extra:
        parts.append(f"extra {extra}")
    details = "; ".join(parts)
    return f"{path} keys must be exactly {_format_keys(expected)} ({details})."


def _validate_required_with_optional_keys(
    value: dict[str, Any],
    *,
    required: set[str],
    optional: set[str],
    path: str,
) -> str | None:
    actual = set(value.keys())
    missing = sorted(required - actual)
    allowed = required | optional
    extra = sorted(actual - allowed)
    if not missing and not extra:
        return None
    parts: list[str] = []
    if missing:
        parts.append(f"missing {missing}")
    if extra:
        parts.append(f"extra {extra}")
    details = "; ".join(parts)
    return (
        f"{path} keys must include {_format_keys(required)} and may include "
        f"{_format_keys(optional)} ({details})."
    )


def _validate_object(value: Any, *, path: str) -> str | None:
    if isinstance(value, dict):
        return None
    return _type_error(path, "object", value)


def _validate_list(value: Any, *, path: str) -> str | None:
    if isinstance(value, list):
        return None
    return _type_error(path, "array", value)


def _validate_string(value: Any, *, path: str) -> str | None:
    if isinstance(value, str):
        return None
    return _type_error(path, "string", value)


def _validate_bool(value: Any, *, path: str) -> str | None:
    if isinstance(value, bool):
        return None
    return _type_error(path, "boolean", value)


def _validate_int(value: Any, *, path: str) -> str | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return None
    return _type_error(path, "integer", value)


def _validate_number(value: Any, *, path: str) -> str | None:
    if (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool):
        return None
    return _type_error(path, "number", value)


def _validate_number_or_null(value: Any, *, path: str) -> str | None:
    if value is None:
        return None
    return _validate_number(value, path=path)


def _validate_object_or_null(value: Any, *, path: str) -> str | None:
    if value is None:
        return None
    return _validate_object(value, path=path)


def _type_error(path: str, expected: str, value: Any) -> str:
    return f"{path} must be {expected}, got {_type_name(value)}."


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _format_keys(keys: set[str]) -> str:
    return "{" + ", ".join(repr(item) for item in sorted(keys)) + "}"


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
