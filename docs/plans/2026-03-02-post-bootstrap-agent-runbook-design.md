# Post-Bootstrap Agent Runbook Design

## Context

`sci-cli-bootstrap` generates a driver skeleton that already satisfies core CLI contract shape, but the generated project does not yet provide a strong, agent-oriented workflow for end-to-end integration from unknown instrument inputs (SDK, docs, CSV/XLSX, TCP protocol, external executable, zip/folder assets).

## Goals

- Make generated skeleton repositories self-guiding for coding agents.
- Require explicit human-intake before backend implementation.
- Support multiple integration modes, not just Python library hookup.
- Preserve strict contract boundary (`driver.py`) while allowing backend flexibility (`backend.py`).
- Ensure end state is locally runnable CLI (`<cli_name>`) with optional GitHub release paths.

## Non-Goals

- Implement hardware-specific integrations inside this framework repo.
- Change core command contract or payload keys.

## Approach Options

### Option A: Expand generated README only (recommended)

Add an agent runbook to generated `README.md` that includes intake gate, discovery process, implementation boundary, verification, local install, and optional release instructions (both `gh` and manual web upload).

Pros:
- Minimal file count increase.
- Immediate discoverability for humans and agents.

Cons:
- README becomes longer.

### Option B: Split runbook into additional docs

Keep README short and add separate `AGENT_RUNBOOK.md` and `RELEASE.md`.

Pros:
- Better topical separation.

Cons:
- Higher risk agent misses critical steps unless prompted.

### Option C: Template + machine-readable spec only

Generate a YAML-only integration specification and keep prose brief.

Pros:
- Structured handoff.

Cons:
- Harder for humans to bootstrap quickly; misses practical command guidance.

## Selected Design

Use Option A plus one additional generated artifact:

1. Generated `README.md` becomes an explicit, deterministic runbook for coding agents.
2. Generated `INTEGRATION_BRIEF.md` captures discovered integration mapping and open questions.

## README Runbook Structure (Generated Project)

1. Mission and hard constraints.
2. Required human intake before coding.
3. Discovery and mapping workflow across unknown input types.
4. Implementation boundary (`backend.py` flexible, `driver.py` stable contract).
5. Verification commands (`pytest`, `sci-cli-conformance`).
6. Local packaging and install endpoint (`python -m build`, `pip install dist/<wheel>`, smoke commands).
7. Release decision gate requiring explicit human confirmation.
8. Release Path A: `gh` CLI workflow.
9. Release Path B: manual GitHub web release upload.

## INTEGRATION_BRIEF Template Structure

- Human-provided sources and locations.
- Control surface type (Python/TCP/serial/EXE/other).
- Parameter/action mapping to core commands.
- Units, ranges, safety limits, and value conversion notes.
- Error taxonomy and expected retry/timeout behavior.
- Open questions requiring human confirmation.

## Testing Impact

- Update scaffold tests to assert `INTEGRATION_BRIEF.md` is generated.
- Keep existing conformance-based scaffold test unchanged to ensure output remains contract-compatible.

## Risks and Mitigations

- Risk: README becomes too verbose.
  - Mitigation: Keep procedural steps concise and command-focused.
- Risk: Agent skips intake.
  - Mitigation: Add hard-gate wording in generated README.
- Risk: Tooling assumptions for release.
  - Mitigation: include both `gh` and manual upload paths.

## Rollout

- Update scaffold template renderers.
- Update scaffold tests.
- Run `pytest` to verify.
