# SCI Agent CLI Core v1 Design

Date: 2026-03-01

## Goal

Create a reusable CLI framework that lets instrument vendors keep any executable name
while enforcing strict nqctl-compatible wire behavior for:

- `capabilities`
- `get`
- `set`
- `ramp`
- `act`

## Decision

Build an independent sibling project (`sci-agent-cli-core`) instead of embedding the
framework into the existing `nanonis-qcodes-controller` package.

## Why this split

- The current repo is product-specific (`nanonis_qcodes_controller`) and has CI/type
  scope tied to that package.
- A protocol framework needs independent versioning and release cadence.
- Non-Nanonis drivers should adopt the framework without inheriting unrelated runtime
  dependencies or docs.

## Architecture

1. `driver.py` defines the abstract interface for the five core operations.
2. `runtime.py` provides shared CLI parsing, command dispatch, JSON/text output, and
   strict error envelope + exit-code mapping.
3. `conformance.py` validates third-party CLIs against the contract.
4. `docs/contract-v1.md` freezes wire-level requirements.

## Non-goals in bootstrap

- Not implementing vendor transport adapters.
- Not implementing optional/non-core commands.
- Not forcing a specific binary name.

## Success criteria

- A minimal demo driver can run all five commands through shared runtime.
- Conformance tool can verify success payload shape and failure envelope.
- Initial tests pass locally.
