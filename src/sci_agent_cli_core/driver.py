from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class BaseInstrumentCliDriver(ABC):
    @abstractmethod
    def capabilities(
        self,
        *,
        include_backend_commands: bool = False,
        backend_match: str | None = None,
    ) -> Mapping[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get(self, parameter: str) -> Mapping[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def set(
        self,
        parameter: str,
        *,
        value: str | None,
        args: Mapping[str, str],
        interval_s: float | None,
        plan_only: bool,
    ) -> Mapping[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def ramp(
        self,
        parameter: str,
        *,
        start: float,
        end: float,
        step: float,
        interval_s: float,
        plan_only: bool,
    ) -> Mapping[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def act(
        self, action_name: str, *, args: Mapping[str, str], plan_only: bool
    ) -> Mapping[str, Any]:
        raise NotImplementedError
