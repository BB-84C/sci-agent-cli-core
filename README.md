# sci-agent-cli-core

Python framework to build instrument CLI drivers with Sci-Agent standard. 

## Scope

This project standardizes exactly five commands:

- `capabilities` to expose all instruments parameters, specs, actions. Output schema see docs. 
- `get` to read an instrument specs, for example: `<cli_driver_name> get bias`
- `set` to set an instrument specs, for example: `<cli_driver_name> set scan_buffer --arg Pixels=512`
- `ramp` to ramp a specs, usually bias/current, or any other specs. Fro example: `<cli_driver_name> ramp bias_v 0.1 0.25 0.01 --interval-s 0.1`
- `act` to make an action to the instrument, for example: `<cli_driver_name> act Scan_Action --arg Scan_action=0 --arg Scan_direction=1`

Drivers can keep any executable name (`nqctl`, `laserctl`, `scopectl`, etc.), but
the command behavior, JSON payloads, and exit codes for the five core commands must
match the contract.


## HOW TO USE: Bootstrap a new driver project

Generate a new standalone driver that already passes core contract checks:

```powershell
sci-cli-bootstrap --output-dir D:\path\<cli_driver_name> --cli-name <cli_driver_name> --package-name <cli_driver_name> --project-name "name-of-your-instrument-driver"
```

Then follow `docs/coding-agent-pipeline.md` to hand off backend hookup to your coding agent.

## What is included

- `sci_agent_cli_core.runtime`: shared argparse runtime with strict error envelope.
- `sci_agent_cli_core.driver`: abstract driver interface for the five core operations.
- `sci_agent_cli_core.conformance`: CLI compatibility checks for external drivers.
- `sci_agent_cli_core.scaffold`: project generator for new instrument driver CLIs.
- `docs/contract-v1.md`: frozen `core-v1` contract reference.
- `docs/coding-agent-pipeline.md`: fast setup flow for coding agents.
- `examples/minimal_demo_driver.py`: starter implementation template.


---
Capabilities item schemas (`<cli_driver_name> capabilities`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://bb-84c.github.io/nqctl/schemas/capabilities-parameter-item.schema.json",
  {
    "title": "nqctl capabilities parameters.items[*]",
    "type": "object",
    "required": [
        "name",
        "label",
        "readable",
        "writable",
        "has_ramp",
        "get_cmd",
        "set_cmd",
        "safety"
    ],
    "properties": {
        "name": { "type": "string", "minLength": 1 },
        "label": { "type": "string" },
        "readable": { "type": "boolean" },
        "writable": { "type": "boolean" },
        "has_ramp": { "type": "boolean" },
        "get_cmd": {
        "oneOf": [
            { "type": "null" },
            {
            "type": "object",
            "required": ["command", "payload_index", "arg_fields", "response_fields"],
            "properties": {
                "command": { "type": "string", "minLength": 1 },
                "payload_index": { "type": "integer", "minimum": 0 },
                "description": { "type": "string" },
                "arg_fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": [
                    "name",
                    "type",
                    "unit",
                    "wire_type",
                    "required",
                    "description",
                    "default"
                    ],
                    "properties": {
                    "name": { "type": "string", "minLength": 1 },
                    "type": { "type": "string" },
                    "unit": { "type": "string" },
                    "wire_type": { "type": "string" },
                    "required": { "type": "boolean" },
                    "description": { "type": "string" },
                    "default": {}
                    },
                    "additionalProperties": false
                }
                },
                "response_fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["index", "name", "type", "unit", "wire_type", "description"],
                    "properties": {
                    "index": { "type": "integer", "minimum": 0 },
                    "name": { "type": "string", "minLength": 1 },
                    "type": { "type": "string" },
                    "unit": { "type": "string" },
                    "wire_type": { "type": "string" },
                    "description": { "type": "string" }
                    },
                    "additionalProperties": false
                }
                }
            },
            "additionalProperties": true
            }
        ]
        },
        "set_cmd": {
        "oneOf": [
            { "type": "null" },
            {
            "type": "object",
            "required": ["command", "arg_fields"],
            "properties": {
                "command": { "type": "string", "minLength": 1 },
                "description": { "type": "string" },
                "arg_fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": [
                    "name",
                    "type",
                    "unit",
                    "wire_type",
                    "required",
                    "description",
                    "default"
                    ],
                    "properties": {
                    "name": { "type": "string", "minLength": 1 },
                    "type": { "type": "string" },
                    "unit": { "type": "string" },
                    "wire_type": { "type": "string" },
                    "required": { "type": "boolean" },
                    "description": { "type": "string" },
                    "default": {}
                    },
                    "additionalProperties": false
                }
                }
            },
            "additionalProperties": true
            }
        ]
        },
        "safety": {
        "oneOf": [
            { "type": "null" },
            {
            "type": "object",
            "required": [
                "min_value",
                "max_value",
                "max_step",
                "max_slew_per_s",
                "cooldown_s",
                "ramp_enabled",
                "ramp_interval_s"
            ],
            "properties": {
                "min_value": { "type": ["number", "null"] },
                "max_value": { "type": ["number", "null"] },
                "max_step": { "type": ["number", "null"] },
                "max_slew_per_s": { "type": ["number", "null"] },
                "cooldown_s": { "type": ["number", "null"] },
                "ramp_enabled": { "type": "boolean" },
                "ramp_interval_s": { "type": ["number", "null"] }
            },
            "additionalProperties": false
            }
        ]
        }
    },
    "additionalProperties": false
  },
  {
    "title": "nqctl capabilities action_commands.items[*]",
    "type": "object",
    "required": ["name", "action_cmd", "safety_mode"],
    "properties": {
        "name": { "type": "string", "minLength": 1 },
        "action_cmd": {
        "type": "object",
        "required": ["command", "arg_fields"],
        "properties": {
            "command": { "type": "string", "minLength": 1 },
            "description": { "type": "string" },
            "arg_fields": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                "name",
                "type",
                "unit",
                "wire_type",
                "required",
                "description",
                "default"
                ],
                "properties": {
                "name": { "type": "string", "minLength": 1 },
                "type": { "type": "string" },
                "unit": { "type": "string" },
                "wire_type": { "type": "string" },
                "required": { "type": "boolean" },
                "description": { "type": "string" },
                "default": {}
                },
                "additionalProperties": false
            }
            }
        },
        "additionalProperties": true
        },
        "safety_mode": {
        "type": "string",
        "enum": ["alwaysAllowed", "guarded", "blocked"]
        }
    },
    "additionalProperties": false
  }
}
```
