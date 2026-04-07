# System GUI

## Status

Planned

## Outcome

Archie should gain first-party graphical interfaces for system operations,
starting with a compact power-and-peripherals control surface and extending to
a Borg-oriented backup GUI once its repository boundary and safety model are
clear.

## Decision Changes

- The first graphical work in Archie should focus on real system operations
  Archie already owns rather than on a generic settings shell.
- Power and power-adjacent peripherals form the first GUI problem space.
- The backup-GUI track remains under this epic until the implementation
  boundary between Archie and `borg-automated-backups` is decided.

## Main Quests

- Define the first-stage power and peripherals control GUI.
- Define the backup GUI scope, ownership boundary, and safety model.

## Acceptance Criteria

- The epic communicates why these GUI tracks belong together as system
  operations work.
- The epic records the unresolved repository-boundary question for the backup
  track.
- The epic exposes a stable `id` and explicit `child_ids`.

## Metadata

### id

system-gui

### child_ids

- system-gui-01
- system-gui-02
