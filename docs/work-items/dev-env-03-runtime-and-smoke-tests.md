# Standardize Runtime Operations And Smoke Tests As Needed

Consolidate the runtime conventions and smoke-test coverage needed to keep the
dev-env VM workflow practical as bootstrap and Archie deployment mature.

## Status

<!--
Use a short prose status for the current state of the work item.
Supported values are `backlog`, `planned`, `doing`, `done`, `cancelled`, and `abandoned`.
`killed` is reserved for GitLab graveyard history when a managed work item is removed from the repository.
-->

Planned

## Outcome

Archie has a lightweight but explicit runtime and validation layer for the dev
env, defined incrementally from real development needs
instead of being overdesigned up front.

## Decision Changes

- The old separation between runtime management and test-pipeline work is not
  useful at this stage. They should be developed together on a need basis.
- Incus runtime standardization should grow only where repeated work or failure
  analysis shows clear benefit.
- Smoke tests should focus on fast, high-signal checks for the dev-env VM
  workflow, not full CI gating or broad UI automation.
- This work remains local-development oriented. CI, QEMU parity, and build
  artifact promotion are still deferred.

## Main Quests

- Define the minimum stable runtime operations that should be standardized after
  work items 1 and 2 uncover the real pain points, such as:
  - rebuild flow
  - reset or teardown flow
  - snapshot usage
  - log retrieval
  - common troubleshooting commands
- Consolidate the Incus lifecycle conventions that are repeatedly needed during
  development into a documented and predictable workflow.
- Define smoke-test scope based on the stabilized bootstrap and deploy flows,
  including checks for:
  - successful provisioning completion
  - successful Archie deployment completion
  - networking availability
  - display manager and session readiness
  - presence of the core Archie desktop stack required for testing
- Decide which checks should be manual commands, which should be scripted, and
  which should remain observational until more maturity exists.
- Define how logs and smoke-test outputs are collected and presented for fast
  debugging.
- Document known blind spots that remain out of scope in this phase, such as
  advanced UI behavior, hardware-specific validation, and release gating.

## Acceptance Criteria

- The dev env has a documented runtime workflow that removes repeated ad hoc
  Incus operations.
- Smoke tests cover the core bootstrap and Archie deployment expectations with
  useful pass or fail outputs.
- Failures provide enough evidence to guide debugging without needing full CI
  integration.
- The work item leaves a clear foundation for later expansion into QEMU parity
  or pipeline automation if that becomes worthwhile.

## Metadata

### id

dev-env-03
