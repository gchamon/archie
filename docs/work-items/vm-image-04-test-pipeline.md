# Test Pipeline

## Status

<!--
Use a short prose status for the current state of the work item.
Supported values are `backlog`, `planned`, `doing`, `done`, `cancelled`, and `abandoned`.
`killed` is reserved for GitLab graveyard history when a managed work item is removed from the repository.
-->

Done

## Outcome

Archie should have a simple automated validation layer for the historical
VM-image pipeline that can run smoke tests against freshly built QEMU images.

## Decision Changes

- The first automated validation layer should focus on smoke-test coverage
  rather than full end-to-end UI testing.
- Validation should check boot success, core Archie process presence,
  networking, package expectations, and failure-log capture.
- The initial phase should establish a lightweight promotion gate instead of a
  heavier benchmarking or hardware-validation program.

## Dependencies

- [`vm-image-03-qemu-image.md`](./vm-image-03-qemu-image.md)

## Main Quests

- Create smoke-test scenarios for produced QEMU images.
- Add unattended boot and install validation plus post-boot health checks.
- Define pass or fail gates and reporting artifacts.
- Establish the baseline reliability threshold for this phase.
- Preserve the initial test scenarios around boot success, core
  processes or services, networking, package presence, and failure-log
  archival.
- Document the test runner scripts, machine-readable reports, integration path,
  and known blind spots.

## Acceptance Criteria

- The pipeline can execute smoke tests against a freshly built QEMU image
  automatically.
- Results are deterministic enough to enforce a promotion gate.
- The minimum gate for this phase is two consecutive successful unattended
  runs.
- Failures provide actionable logs for root-cause analysis.

## Metadata

### id

vm-image-04
