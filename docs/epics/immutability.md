# Immutability

## Status

Planned

## Outcome

Archie should have a decision-backed immutability track that determines whether
an `arkdep`-managed base system is a practical and maintainable way to handle
system dependencies, updates, and rollback without disrupting the current host
workflow.


## Work items

- [immutability-01-arkdep-evaluation-and-poc](/docs/work-items/immutability-01-arkdep-evaluation-and-poc.md)

## Decision Changes

- `immutability` is the canonical epic name for Archie work around immutable or
  image-style system management.
- This track is separate from the completed deployment-management work because
  it evaluates a new system-management model rather than changing Stow
  ownership boundaries.
- `arkdep` is the primary implementation candidate to evaluate first.
- A disposable VM proof of concept is required before Archie commits to any
  immutability architecture changes on a real workstation.
- A delayed-update wrapper around Arch Linux Archive package versions remains an
  explicit fallback if `arkdep` is rejected or deferred.

## Main Quests

- Evaluate `arkdep` against Archie's current architecture and operator
  expectations.
- Run an isolated proof of concept in a disposable VM derived from the current
  reproducible image workflow.
- Decide whether to proceed with an `arkdep` adoption track or fall back to a
  constrained delayed-update manager built around Arch Linux Archive data.

## Acceptance Criteria

- The epic explains why immutability is a distinct planning track for Archie.
- The epic states that `arkdep` evaluation is the first milestone instead of
  assuming adoption.
- The epic exposes a stable `id` and explicit `child_ids`.

## Metadata

### id

immutability

### child_ids

- immutability-01

### priority

high
