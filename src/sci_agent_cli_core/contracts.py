from __future__ import annotations

from typing import Any

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_POLICY_BLOCKED = 2
EXIT_INVALID_INPUT = 3
EXIT_COMMAND_UNAVAILABLE = 4
EXIT_CONNECTION_FAILED = 5

CORE_COMMANDS: tuple[str, ...] = ("capabilities", "get", "set", "ramp", "act")


def build_error_payload(*, exit_code: int, error_type: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "type": str(error_type),
            "message": str(message),
        },
        "exit_code": int(exit_code),
    }
