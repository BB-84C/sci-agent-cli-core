from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

import pytest
from sci_agent_cli_core import conformance
from sci_agent_cli_core.conformance import main


def test_conformance_passes_for_demo_driver() -> None:
    project_root = Path(__file__).resolve().parents[1]
    demo_driver = project_root / "examples" / "minimal_demo_driver.py"
    command = f"{sys.executable} {demo_driver}"

    exit_code = main(
        [
            "--command",
            command,
            "--get-parameter",
            "bias_v",
            "--set-parameter",
            "bias_v",
            "--set-arg",
            "Bias_value_V=0.1",
            "--ramp-parameter",
            "bias_v",
            "--ramp-start",
            "0.0",
            "--ramp-end",
            "0.2",
            "--ramp-step",
            "0.05",
            "--action-name",
            "Scan_Action",
            "--action-arg",
            "Scan_action=0",
        ]
    )

    assert exit_code == 0


def test_contract_doc_lists_core_commands() -> None:
    project_root = Path(__file__).resolve().parents[1]
    text = (project_root / "docs" / "contract-v1.md").read_text(encoding="utf-8")
    assert "capabilities" in text
    assert "get <parameter>" in text
    assert "set <parameter>" in text
    assert "ramp <parameter>" in text
    assert "act <action_name>" in text


def _valid_capabilities_payload() -> dict[str, Any]:
    return {
        "parameters": {
            "count": 1,
            "items": [
                {
                    "name": "bias_v",
                    "label": "Bias Value",
                    "readable": True,
                    "writable": True,
                    "has_ramp": True,
                    "get_cmd": {
                        "command": "Instrument.ValueGet",
                        "payload_index": 0,
                        "arg_fields": [],
                        "response_fields": [
                            {
                                "index": 0,
                                "name": "Bias_value_V",
                                "type": "float",
                                "unit": "V",
                                "wire_type": "f",
                                "description": "Measured bias value",
                            }
                        ],
                    },
                    "set_cmd": {
                        "command": "Instrument.ValueSet",
                        "arg_fields": [
                            {
                                "name": "Bias_value_V",
                                "type": "float",
                                "unit": "V",
                                "wire_type": "f",
                                "required": True,
                                "description": "Target bias value",
                                "default": None,
                            }
                        ],
                    },
                    "safety": {
                        "min_value": None,
                        "max_value": None,
                        "max_step": None,
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
                    "action_cmd": {
                        "command": "Instrument.Action",
                        "arg_fields": [
                            {
                                "name": "Scan_action",
                                "type": "int",
                                "unit": "",
                                "wire_type": "i",
                                "required": False,
                                "description": "Action mode",
                                "default": 0,
                            }
                        ],
                    },
                    "safety_mode": "guarded",
                }
            ],
        },
    }


def _valid_get_payload() -> dict[str, Any]:
    return {
        "parameter": "bias_v",
        "value": 0.1,
        "fields": {"Bias_value_V": 0.1},
        "timestamp_utc": "2026-03-02T00:00:00Z",
    }


def _valid_set_payload() -> dict[str, Any]:
    return {
        "parameter": "bias_v",
        "plan_only": True,
        "result": {"ok": True},
        "timestamp_utc": "2026-03-02T00:00:00Z",
    }


def _valid_ramp_payload() -> dict[str, Any]:
    return {
        "parameter": "bias_v",
        "start_value": 0.0,
        "end_value": 0.2,
        "step_value": 0.05,
        "interval_s": 0.1,
        "plan": {"steps": [0.0, 0.05, 0.1, 0.15, 0.2]},
        "applied": False,
        "report": {"steps": 5},
        "timestamp_utc": "2026-03-02T00:00:00Z",
    }


def _valid_act_payload() -> dict[str, Any]:
    return {
        "action": "Scan_Action",
        "plan_only": True,
        "result": {"status": "queued"},
        "timestamp_utc": "2026-03-02T00:00:00Z",
    }


Validator = Callable[[dict[str, Any]], str | None]
PayloadFactory = Callable[[], dict[str, Any]]


def _assert_validator_error(
    validator: Validator,
    payload: dict[str, Any],
    expected_fragments: tuple[str, ...],
) -> None:
    error = validator(payload)
    assert isinstance(error, str)
    lowered_error = error.lower()
    for fragment in expected_fragments:
        assert fragment.lower() in lowered_error


def _invalid_capabilities_extra_parameter_item_keys() -> dict[str, Any]:
    payload = _valid_capabilities_payload()
    parameter_item = deepcopy(payload["parameters"]["items"][0])
    parameter_item["extra"] = "not-allowed"
    payload["parameters"] = {
        **deepcopy(payload["parameters"]),
        "items": [parameter_item],
    }
    return payload


def _invalid_capabilities_invalid_safety_mode() -> dict[str, Any]:
    payload = _valid_capabilities_payload()
    action_item = deepcopy(payload["action_commands"]["items"][0])
    action_item["safety_mode"] = "unsafe-mode"
    payload["action_commands"] = {
        **deepcopy(payload["action_commands"]),
        "items": [action_item],
    }
    return payload


def _invalid_capabilities_malformed_arg_field_descriptor() -> dict[str, Any]:
    payload = _valid_capabilities_payload()
    parameter_item = deepcopy(payload["parameters"]["items"][0])
    set_cmd = deepcopy(parameter_item["set_cmd"])
    set_cmd["arg_fields"] = [{"name": "Bias_value_V"}]
    parameter_item["set_cmd"] = set_cmd
    payload["parameters"] = {
        **deepcopy(payload["parameters"]),
        "items": [parameter_item],
    }
    return payload


def _invalid_get_extra_top_level_key() -> dict[str, Any]:
    return {**_valid_get_payload(), "extra": 1}


def _invalid_set_plan_only_non_bool() -> dict[str, Any]:
    return {**_valid_set_payload(), "plan_only": "true"}


def _invalid_ramp_plan_non_object() -> dict[str, Any]:
    return {**_valid_ramp_payload(), "plan": ["not", "an", "object"]}


def _invalid_act_result_non_object() -> dict[str, Any]:
    return {**_valid_act_payload(), "result": ["not", "an", "object"]}


@pytest.mark.parametrize(
    ("validator", "payload_factory", "expected_fragments"),
    [
        (
            conformance._validate_capabilities_payload,
            _invalid_capabilities_extra_parameter_item_keys,
            (
                "capabilities.parameters.items[0]",
                "keys must be exactly",
                "extra ['extra']",
            ),
        ),
        (
            conformance._validate_capabilities_payload,
            _invalid_capabilities_invalid_safety_mode,
            (
                "capabilities.action_commands.items[0].safety_mode",
                "must be one of",
            ),
        ),
        (
            conformance._validate_capabilities_payload,
            _invalid_capabilities_malformed_arg_field_descriptor,
            (
                "capabilities.parameters.items[0].set_cmd.arg_fields[0]",
                "keys must be exactly",
                "missing",
            ),
        ),
        (
            conformance._validate_get_payload,
            _invalid_get_extra_top_level_key,
            ("get keys must be exactly", "extra ['extra']"),
        ),
        (
            conformance._validate_set_payload,
            _invalid_set_plan_only_non_bool,
            ("set.plan_only", "must be boolean"),
        ),
        (
            conformance._validate_ramp_payload,
            _invalid_ramp_plan_non_object,
            ("ramp.plan must be object", "got array"),
        ),
        (
            conformance._validate_act_payload,
            _invalid_act_result_non_object,
            ("act.result must be object", "got array"),
        ),
    ],
    ids=[
        "capabilities_extra_parameter_item_keys",
        "capabilities_invalid_safety_mode",
        "capabilities_malformed_arg_field_descriptor",
        "get_extra_top_level_key",
        "set_plan_only_non_bool",
        "ramp_plan_non_object",
        "act_result_non_object",
    ],
)
def test_strict_schema_rejects_invalid_payloads(
    validator: Validator,
    payload_factory: PayloadFactory,
    expected_fragments: tuple[str, ...],
) -> None:
    _assert_validator_error(
        validator=validator,
        payload=payload_factory(),
        expected_fragments=expected_fragments,
    )


def test_capabilities_strict_schema_accepts_valid_payload() -> None:
    assert conformance._validate_capabilities_payload(_valid_capabilities_payload()) is None


def test_get_strict_schema_accepts_valid_payload() -> None:
    assert conformance._validate_get_payload(_valid_get_payload()) is None


def test_set_strict_schema_accepts_valid_payload() -> None:
    assert conformance._validate_set_payload(_valid_set_payload()) is None


def test_ramp_strict_schema_accepts_valid_payload() -> None:
    assert conformance._validate_ramp_payload(_valid_ramp_payload()) is None


def test_act_strict_schema_accepts_valid_payload() -> None:
    assert conformance._validate_act_payload(_valid_act_payload()) is None


def test_main_fails_when_set_parameter_missing_set_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_results: list[conformance.CheckResult] = []

    monkeypatch.setattr(
        conformance,
        "_check_capabilities",
        lambda _base_command: conformance.CheckResult("capabilities", True, "ok"),
    )
    monkeypatch.setattr(
        conformance,
        "_check_set",
        lambda *_args, **_kwargs: pytest.fail("_check_set should not be called"),
    )
    monkeypatch.setattr(
        conformance,
        "_print_results",
        lambda *, results, as_json: captured_results.extend(results),
    )

    exit_code = main(
        [
            "--command",
            "demo-driver",
            "--set-parameter",
            "bias_v",
            "--skip-error-check",
        ]
    )

    assert exit_code == 1
    set_result = next((item for item in captured_results if item.name == "set"), None)
    assert set_result is not None
    assert set_result.ok is False
    assert "--set-value" in set_result.details
    assert "--set-arg" in set_result.details
