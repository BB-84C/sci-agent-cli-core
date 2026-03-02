from __future__ import annotations

import json
from datetime import datetime, timezone

from sci_agent_cli_core import EXIT_INVALID_INPUT, EXIT_OK
from sci_agent_cli_core.contracts import build_error_payload
from sci_agent_cli_core.driver import BaseInstrumentCliDriver
from sci_agent_cli_core.errors import PolicyBlockedError
from sci_agent_cli_core.runtime import run_cli


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class FakeDriver(BaseInstrumentCliDriver):
    def __init__(self, *, block_get: bool = False):
        self.block_get = block_get

    def capabilities(
        self, *, include_backend_commands: bool = False, backend_match: str | None = None
    ):
        del include_backend_commands
        del backend_match
        return {
            "parameters": {"count": 1, "items": [{"name": "bias_v"}]},
            "action_commands": {"count": 0, "items": []},
        }

    def get(self, parameter: str):
        if self.block_get:
            raise PolicyBlockedError("blocked")
        return {
            "parameter": parameter,
            "value": 0.1,
            "fields": {"Bias_value_V": 0.1},
            "timestamp_utc": _now_utc_iso(),
        }

    def set(
        self,
        parameter: str,
        *,
        value: str | None,
        args: dict[str, str],
        interval_s: float | None,
        plan_only: bool,
    ):
        del value
        del args
        del interval_s
        return {
            "parameter": parameter,
            "plan_only": plan_only,
            "result": {"accepted": True},
            "timestamp_utc": _now_utc_iso(),
        }

    def ramp(
        self,
        parameter: str,
        *,
        start: float,
        end: float,
        step: float,
        interval_s: float,
        plan_only: bool,
    ):
        del plan_only
        return {
            "parameter": parameter,
            "start_value": start,
            "end_value": end,
            "step_value": step,
            "interval_s": interval_s,
            "plan": {"count": 2},
            "applied": False,
            "report": None,
            "timestamp_utc": _now_utc_iso(),
        }

    def act(self, action_name: str, *, args: dict[str, str], plan_only: bool):
        del args
        return {
            "action": action_name,
            "plan_only": plan_only,
            "result": {"accepted": True},
            "timestamp_utc": _now_utc_iso(),
        }


def test_package_imports() -> None:
    import sci_agent_cli_core

    assert sci_agent_cli_core.__version__


def test_error_payload_shape() -> None:
    payload = build_error_payload(exit_code=3, error_type="ValueError", message="bad input")
    assert payload["ok"] is False
    assert payload["error"]["type"] == "ValueError"
    assert payload["exit_code"] == 3


def test_runtime_capabilities_command(capsys) -> None:
    code = run_cli(FakeDriver(), ["capabilities", "--json"], prog="democtl")
    assert code == EXIT_OK
    stdout = capsys.readouterr().out
    payload = json.loads(stdout)
    assert set(payload.keys()) == {"parameters", "action_commands"}


def test_runtime_rejects_duplicate_arg_keys(capsys) -> None:
    code = run_cli(
        FakeDriver(),
        ["set", "bias_v", "--arg", "Bias_value_V=0.1", "--arg", "Bias_value_V=0.2", "--json"],
        prog="democtl",
    )
    assert code == EXIT_INVALID_INPUT
    stdout = capsys.readouterr().out
    payload = json.loads(stdout)
    assert payload["ok"] is False
    assert payload["exit_code"] == EXIT_INVALID_INPUT


def test_runtime_maps_policy_blocked_errors(capsys) -> None:
    code = run_cli(FakeDriver(block_get=True), ["get", "bias_v", "--json"], prog="democtl")
    assert code == 2
    stdout = capsys.readouterr().out
    payload = json.loads(stdout)
    assert payload["error"]["type"] == "PolicyBlockedError"
