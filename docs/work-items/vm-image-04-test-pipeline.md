# Work Item: Test Pipeline

<!--toc:start-->

- [Work Item: Test Pipeline](#work-item-test-pipeline)
  - [Goal](#goal)
  - [Scope](#scope)
  - [Initial Test Scenarios](#initial-test-scenarios)
  - [Out of Scope](#out-of-scope)
  - [Inputs](#inputs)
  - [Deliverables](#deliverables)
  - [Acceptance Criteria](#acceptance-criteria)
  - [Dependencies](#dependencies)
<!--toc:end-->

## Goal
Define and implement a simple automated validation pipeline for Archie VM images.

## Scope
- Create smoke test scenarios for produced QEMU images.
- Add unattended boot/install validation and post-boot health checks.
- Define pass/fail gates and reporting artifacts.
- Establish baseline reliability threshold for this phase.

## Initial Test Scenarios
- Scenario 1: image boots successfully to expected system state.
- Scenario 2: Archie core processes/services are present (session, bar, notification stack).
- Scenario 3: networking is available after boot.
- Scenario 4: selected package groups are present; excluded groups are absent.
- Scenario 5: provisioning artifacts/logs are archived on failure.

## Out of Scope
- Full end-to-end UI testing.
- Hardware-specific GPU validation on physical devices.
- Performance benchmarking.

## Inputs
- Image build outputs from the `QEMU_IMAGE` work item.
- Installer and provisioning logs from earlier work items.

## Deliverables
- Test runner scripts for smoke scenarios.
- Machine-readable test report format (pass/fail + key diagnostics).
- CI/CD integration path for scheduled or on-demand execution.
- Documentation of test matrix and known blind spots.

## Acceptance Criteria
- Pipeline can execute smoke tests against freshly built QEMU image automatically.
- Results are deterministic enough to enforce a promotion gate.
- Minimum gate for this phase: 2 consecutive successful unattended runs.
- Failures provide actionable logs for root-cause analysis.

## Dependencies
- `docs/work-items/vm-image-03-qemu-image.md`.
