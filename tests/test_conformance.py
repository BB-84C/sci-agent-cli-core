from __future__ import annotations

import sys
from pathlib import Path

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
