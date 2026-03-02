from __future__ import annotations

from sci_agent_cli_core.contracts import (
    EXIT_COMMAND_UNAVAILABLE,
    EXIT_CONNECTION_FAILED,
    EXIT_FAILED,
    EXIT_INVALID_INPUT,
    EXIT_POLICY_BLOCKED,
)


class CliCoreError(Exception):
    exit_code = EXIT_FAILED
    error_type = "CliCoreError"

    def __init__(
        self, message: str, *, exit_code: int | None = None, error_type: str | None = None
    ):
        super().__init__(str(message))
        if exit_code is not None:
            self.exit_code = int(exit_code)
        if error_type is not None:
            self.error_type = str(error_type)


class PolicyBlockedError(CliCoreError):
    exit_code = EXIT_POLICY_BLOCKED
    error_type = "PolicyBlockedError"


class InvalidInputError(CliCoreError):
    exit_code = EXIT_INVALID_INPUT
    error_type = "InvalidInputError"


class CommandUnavailableError(CliCoreError):
    exit_code = EXIT_COMMAND_UNAVAILABLE
    error_type = "CommandUnavailableError"


class ConnectionFailedError(CliCoreError):
    exit_code = EXIT_CONNECTION_FAILED
    error_type = "ConnectionFailedError"
