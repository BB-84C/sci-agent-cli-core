# ruff: noqa: E402
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sci_agent_cli_core.driver import BaseInstrumentCliDriver
from sci_agent_cli_core.errors import InvalidInputError
from sci_agent_cli_core.runtime import run_cli


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class DemoDriver(BaseInstrumentCliDriver):
    def capabilities(
        self,
        *,
        include_backend_commands: bool = False,
        backend_match: str | None = None,
    ) -> dict[str, Any]:
        del include_backend_commands
        del backend_match
        return {
            "parameters": {
                "count": 1,
                "items": [
                    {
                        "name": "bias_v",
                        "label": "Bias",
                        "readable": True,
                        "writable": True,
                        "has_ramp": True,
                        "get_cmd": {
                            "command": "Bias.Get",
                            "payload_index": 0,
                            "arg_fields": [],
                            "response_fields": [],
                        },
                        "set_cmd": {"command": "Bias.Set", "arg_fields": []},
                        "safety": {
                            "min_value": -10.0,
                            "max_value": 10.0,
                            "max_step": 1.0,
                            "max_slew_per_s": None,
                            "cooldown_s": None,
                            "ramp_enabled": True,
                            "ramp_interval_s": 0.1,
                        },
                    }
                ],
            },
            "action_commands": {
                "count": 1,
                "items": [
                    {
                        "name": "Scan_Action",
                        "action_cmd": {"command": "Scan_Action", "arg_fields": []},
                        "safety_mode": "guarded",
                    }
                ],
            },
        }

    def get(self, parameter: str) -> dict[str, Any]:
        if parameter != "bias_v":
            raise InvalidInputError(f"Unknown parameter: {parameter}")
        fields = {"Bias_value_V": 0.12}
        return {
            "parameter": parameter,
            "value": 0.12,
            "fields": fields,
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
    ) -> dict[str, Any]:
        if parameter != "bias_v":
            raise InvalidInputError(f"Unknown parameter: {parameter}")
        if value is None and "Bias_value_V" not in args:
            raise InvalidInputError("Provide positional <value> or --arg Bias_value_V=<value>.")
        target = float(value) if value is not None else float(args["Bias_value_V"])
        return {
            "parameter": parameter,
            "plan_only": bool(plan_only),
            "result": {
                "accepted": True,
                "target": target,
                "interval_s": interval_s,
            },
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
    ) -> dict[str, Any]:
        if parameter != "bias_v":
            raise InvalidInputError(f"Unknown parameter: {parameter}")
        plan = {
            "steps": [start, end],
            "count": 2,
            "interval_s": interval_s,
            "plan_only": bool(plan_only),
        }
        return {
            "parameter": parameter,
            "start_value": start,
            "end_value": end,
            "step_value": step,
            "interval_s": interval_s,
            "plan": plan,
            "applied": False,
            "report": None,
            "timestamp_utc": _now_utc_iso(),
        }

    def act(self, action_name: str, *, args: dict[str, str], plan_only: bool) -> dict[str, Any]:
        if action_name != "Scan_Action":
            raise InvalidInputError(f"Unknown action: {action_name}")
        return {
            "action": action_name,
            "plan_only": bool(plan_only),
            "result": {
                "accepted": True,
                "args": dict(args),
            },
            "timestamp_utc": _now_utc_iso(),
        }


def main() -> int:
    return run_cli(DemoDriver(), prog="democtl")


if __name__ == "__main__":
    raise SystemExit(main())
