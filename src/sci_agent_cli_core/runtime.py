from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from typing import Any

from sci_agent_cli_core.contracts import (
    EXIT_FAILED,
    EXIT_INVALID_INPUT,
    EXIT_OK,
    build_error_payload,
)
from sci_agent_cli_core.driver import BaseInstrumentCliDriver
from sci_agent_cli_core.errors import CliCoreError

_NEGATIVE_NUMERIC_TOKEN_RE = re.compile(
    r"^-((\d+\.?\d*)|(\.\d+))([eE][-+]?\d+)?$|^-inf$|^-nan$",
    re.IGNORECASE,
)


def run_cli(
    driver: BaseInstrumentCliDriver,
    argv: Sequence[str] | None = None,
    *,
    prog: str = "instrumentctl",
) -> int:
    normalized_argv = _normalize_help_args(sys.argv[1:] if argv is None else argv)
    parser = build_parser(prog=prog)
    args = parser.parse_args(normalized_argv)

    try:
        payload = _dispatch(driver=driver, args=args)
        _print_payload(payload, as_json=args.json)
        return EXIT_OK
    except CliCoreError as exc:
        return _emit_error(
            args,
            exit_code=exc.exit_code,
            message=str(exc),
            error_type=exc.error_type,
        )
    except ValueError as exc:
        return _emit_error(
            args,
            exit_code=EXIT_INVALID_INPUT,
            message=str(exc),
            error_type=type(exc).__name__,
        )
    except KeyboardInterrupt:
        return _emit_error(
            args,
            exit_code=EXIT_FAILED,
            message="Interrupted by user.",
            error_type="KeyboardInterrupt",
        )
    except Exception as exc:  # pragma: no cover
        return _emit_error(
            args,
            exit_code=EXIT_FAILED,
            message=f"Unexpected error: {exc}",
            error_type=type(exc).__name__,
        )


def build_parser(*, prog: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Core-compatible instrument CLI runtime.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            f"  {prog} capabilities\n"
            f"  {prog} get bias_v\n"
            f"  {prog} set bias_v --arg Bias_value_V=0.12\n"
            f"  {prog} ramp bias_v 0.1 0.3 0.01 --interval-s 0.1\n"
            f"  {prog} act Scan_Action --arg Scan_action=0"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_capabilities = subparsers.add_parser(
        "capabilities",
        help="Show parameter/action command capabilities.",
    )
    _add_json_arg(parser_capabilities)
    parser_capabilities.add_argument(
        "--include-backend-commands",
        action="store_true",
        help="Optionally include backend command inventory.",
    )
    parser_capabilities.add_argument("--backend-match", help="Optional backend filter token.")

    parser_get = subparsers.add_parser("get", help="Read one parameter.")
    _add_json_arg(parser_get)
    parser_get.add_argument("parameter", help="Parameter name.")

    parser_set = subparsers.add_parser(
        "set",
        help="Apply guarded structured write.",
    )
    _add_json_arg(parser_set)
    parser_set.add_argument("parameter", help="Writable parameter name.")
    parser_set.add_argument("value", nargs="?", help="Optional shorthand scalar value.")
    parser_set.add_argument(
        "--arg",
        action="append",
        default=[],
        help="Parameter argument override (repeatable): key=value",
    )
    parser_set.add_argument("--interval-s", type=float, help="Optional interval for slew checks.")
    parser_set.add_argument("--plan-only", action="store_true", help="Show plan only.")

    parser_ramp = subparsers.add_parser(
        "ramp",
        help="Apply explicit guarded ramp.",
    )
    _add_json_arg(parser_ramp)
    parser_ramp.add_argument("parameter", help="Writable parameter name.")
    parser_ramp.add_argument("start", help="Ramp start value.")
    parser_ramp.add_argument("end", help="Ramp end value.")
    parser_ramp.add_argument("step", help="Positive ramp step value.")
    parser_ramp.add_argument(
        "--interval-s", type=float, required=True, help="Step interval in seconds."
    )
    parser_ramp.add_argument("--plan-only", action="store_true", help="Show ramp plan only.")

    parser_act = subparsers.add_parser(
        "act",
        help="Invoke one manifest action command.",
    )
    _add_json_arg(parser_act)
    parser_act.add_argument("action_name", help="Action name from action manifest section.")
    parser_act.add_argument(
        "--arg",
        action="append",
        default=[],
        help="Action argument override (repeatable): key=value",
    )
    parser_act.add_argument("--plan-only", action="store_true", help="Show action plan only.")

    _configure_negative_number_parsing(parser)
    return parser


def _dispatch(driver: BaseInstrumentCliDriver, *, args: argparse.Namespace) -> Mapping[str, Any]:
    command = str(args.command)
    if command == "capabilities":
        payload = driver.capabilities(
            include_backend_commands=bool(args.include_backend_commands),
            backend_match=args.backend_match,
        )
        return _require_mapping(payload, command=command)

    if command == "get":
        parameter = _normalize_name(args.parameter, label="parameter")
        payload = driver.get(parameter)
        return _require_mapping(payload, command=command)

    if command == "set":
        parameter = _normalize_name(args.parameter, label="parameter")
        parsed_args = _parse_action_args(raw_args=tuple(args.arg))
        interval_s = None if args.interval_s is None else float(args.interval_s)
        if interval_s is not None and interval_s < 0:
            raise ValueError("--interval-s must be non-negative.")
        payload = driver.set(
            parameter,
            value=args.value,
            args=parsed_args,
            interval_s=interval_s,
            plan_only=bool(args.plan_only),
        )
        return _require_mapping(payload, command=command)

    if command == "ramp":
        parameter = _normalize_name(args.parameter, label="parameter")
        start_value = _parse_float_arg(name="start", raw_value=args.start)
        end_value = _parse_float_arg(name="end", raw_value=args.end)
        step_value = abs(_parse_float_arg(name="step", raw_value=args.step))
        if step_value <= 0:
            raise ValueError("step magnitude must be positive.")
        interval_s = float(args.interval_s)
        if interval_s < 0:
            raise ValueError("--interval-s must be non-negative.")
        payload = driver.ramp(
            parameter,
            start=start_value,
            end=end_value,
            step=step_value,
            interval_s=interval_s,
            plan_only=bool(args.plan_only),
        )
        return _require_mapping(payload, command=command)

    if command == "act":
        action_name = _normalize_name(args.action_name, label="action_name")
        parsed_args = _parse_action_args(raw_args=tuple(args.arg))
        payload = driver.act(action_name, args=parsed_args, plan_only=bool(args.plan_only))
        return _require_mapping(payload, command=command)

    raise ValueError(f"Unsupported command: {command}")


def _normalize_help_args(argv: Sequence[str]) -> list[str]:
    tokens = ["--help" if token == "-help" else str(token) for token in argv]
    if not tokens:
        return tokens
    if tokens[0] in {"-h", "--help"}:
        if len(tokens) == 1:
            return ["--help"]
        if tokens[1].startswith("-"):
            return ["--help", *tokens[1:]]
        return [*tokens[1:], "--help"]
    return tokens


def _configure_negative_number_parsing(parser: argparse.ArgumentParser) -> None:
    parser._negative_number_matcher = _NEGATIVE_NUMERIC_TOKEN_RE
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for subparser in action.choices.values():
                _configure_negative_number_parsing(subparser)


def _add_json_arg(parser: argparse.ArgumentParser) -> None:
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument(
        "--json",
        action="store_true",
        dest="json",
        default=True,
        help="Print JSON output (default).",
    )
    format_group.add_argument(
        "--text",
        action="store_false",
        dest="json",
        help="Print text output.",
    )


def _parse_action_args(*, raw_args: tuple[str, ...]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_arg in raw_args:
        token = str(raw_arg).strip()
        if not token or "=" not in token:
            raise ValueError("Each --arg entry must follow key=value format.")
        key, raw_value = token.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("Argument key cannot be empty.")
        if key in parsed:
            raise ValueError(f"Duplicate --arg key: {key}")
        parsed[key] = raw_value.strip()
    return parsed


def _parse_float_arg(*, name: str, raw_value: Any) -> float:
    try:
        value = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc
    if value != value:
        raise ValueError(f"{name} must not be NaN.")
    return value


def _normalize_name(value: Any, *, label: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{label} cannot be empty.")
    return normalized


def _require_mapping(value: Any, *, command: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Driver returned non-mapping payload for '{command}'.")
    return value


def _emit_error(
    args: argparse.Namespace,
    *,
    exit_code: int,
    message: str,
    error_type: str,
) -> int:
    payload = build_error_payload(exit_code=exit_code, error_type=error_type, message=message)
    if bool(getattr(args, "json", False)):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(message, file=sys.stderr)
    return int(exit_code)


def _print_payload(payload: Mapping[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(_json_safe(dict(payload)), indent=2))
        return

    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            print(f"{key}: {json.dumps(_json_safe(value), ensure_ascii=True)}")
        else:
            print(f"{key}: {value}")


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]

    item_method = getattr(value, "item", None)
    if callable(item_method):
        try:
            return _json_safe(item_method())
        except Exception:
            return str(value)

    return str(value)
