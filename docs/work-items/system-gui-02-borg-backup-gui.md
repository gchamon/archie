# Design A Borg Backup GUI And Decide Its Repository Boundary

Define the backup GUI track for Archie around the existing Borg workflow, while
explicitly deciding whether the resulting implementation belongs in Archie or
in `borg-automated-backups`.

## Status

<!--
Use a short prose status for the current state of the work item.
Supported values are `backlog`, `planned`, `doing`, `done`, `cancelled`, and `abandoned`.
`killed` is reserved for GitLab graveyard history when a managed work item is removed from the repository.
-->

Planned

## Outcome

Archie has a concrete design for a Borg-oriented backup GUI and an explicit
decision record for whether it should be implemented here as Archie-owned code
or upstreamed as a reusable module in
`https://github.com/gchamon/borg-automated-backups`.

## Decision Changes

- The backup GUI belongs to the `system-gui` epic because it is part of the
  intended Archie user experience even if implementation later moves to another
  repository.
- This work item is design-first and boundary-first. It should not assume the
  current repo is automatically the final implementation home.
- Repository placement should be decided based on ownership of backup logic,
  reuse potential outside Archie, and how much Archie-specific session
  integration the GUI requires.
- The GUI should reflect the real Borg workflow Archie uses, not an abstract
  backup dashboard detached from the existing scripts, timers, and recovery
  guidance.
- Backup safety is more important than convenience; destructive or confusing
  actions must be made explicit in the eventual design.

## Dependencies

- [Backup and Restore Guide](../BACKUP_AND_RESTORE.md) defines the current
  Archie Borg workflow the GUI must represent or wrap.
- [Work Item 1](system-gui-01-power-and-peripherals-control.md) is not a hard
  technical dependency, but it establishes the first GUI conventions for this
  epic and should inform shared UX expectations where useful.

## Scope Notes

Included:

- Define the user-facing backup and restore tasks that deserve GUI support.
- Decide whether Archie or `borg-automated-backups` should own the
  implementation.
- Define the backend contract the GUI would need from whichever repository owns
  the logic.
- Define the safety model for running, inspecting, and restoring backups.

Not included:

- Full implementation of the GUI.
- Replacing Borg CLI capabilities that are better kept as advanced manual
  operations.
- Cross-machine backup orchestration beyond Archie’s current supported setup.

## Main Quests

- Inventory the current Archie backup flow, including:
  - backup creation
  - backup status and recency visibility
  - repository health and error visibility
  - restore guidance and restore execution boundaries
- Define the smallest useful GUI scope for backup operations, including which
  flows should be available initially and which should stay CLI-only.
- Decide the implementation home by comparing Archie and
  `borg-automated-backups` against at least:
  - reuse outside Archie
  - ownership of Borg orchestration logic
  - Archie-specific UI or session integration needs
  - maintenance burden if the GUI and backend live in different repositories
- Define the backend interface the GUI expects, such as structured status
  output, progress events, dry-run support, or restore plan generation.
- Define the risk boundaries for destructive actions, including:
  - restore target selection
  - overwrite semantics
  - passphrase or secret handling
  - failure recovery and operator confirmation
- Define how the GUI should present historical backup information, in-progress
  runs, and actionable failure states without hiding important Borg details.

## Acceptance Criteria

- Archie has a planned backup GUI scope that is specific enough to implement
  without rediscovering the basic user flows.
- The repository boundary decision between Archie and
  `borg-automated-backups` is made explicitly with reasons.
- The work item identifies the backend capabilities and safety constraints the
  implementation must satisfy before GUI coding begins.

## Metadata

### id

system-gui-02
