# Dev Env

## Status

Planned

## Outcome

Archie should have a repeatable development-environment workflow around an
Incus-managed Arch guest that can bootstrap the VM, deploy Archie into it, and
run the minimum runtime and smoke checks needed to keep iteration practical.

## Decision Changes

- `dev-env` is the canonical name for the repeatable development-environment
  initiative and replaces the older `reproducible-environment` label.
- The development-environment track should focus on an Incus-managed Arch VM
  instead of reviving the older unattended image-pipeline effort.
- Runtime operations and smoke-test guidance should be added only after the
  bootstrap and deployment automation path is clear.

## Main Quests

- Bootstrap the Incus-managed Arch guest to a graphical-ready baseline.
- Automate Archie deployment into that guest.
- Define runtime operations and smoke-test expectations that support the
  resulting workflow.

## Acceptance Criteria

- The epic explains the intended Incus-based development loop clearly enough to
  orient future work.
- The epic records the rename from `reproducible-environment` to `dev-env`.
- The epic exposes a stable `id` and explicit `child_ids`.

## Metadata

### id

dev-env

### child_ids

- dev-env-01
- dev-env-02
- dev-env-03

### priority

high
