# System GUI

## Status

Planned

## Outcome

Archie should gain first-party graphical interfaces for system operations,
starting with a compact power-and-peripherals control surface and extending to
a Borg-oriented backup GUI once its repository boundary and safety model are
clear.


## Work items

- [system-gui-01-power-and-peripherals-control](/docs/work-items/system-gui-01-power-and-peripherals-control.md)
- [system-gui-02-borg-backup-gui](/docs/work-items/system-gui-02-borg-backup-gui.md)
- [system-gui-03-monitor-output-widget](/docs/work-items/system-gui-03-monitor-output-widget.md)
- [system-gui-04-lid-close-policy-widget](/docs/work-items/system-gui-04-lid-close-policy-widget.md)
- [system-gui-05-desktop-controls-and-applet](/docs/work-items/system-gui-05-desktop-controls-and-applet.md)
- [system-gui-06-waybar-power-and-theme-controls](/docs/work-items/system-gui-06-waybar-power-and-theme-controls.md)

## Decision Changes

- The first graphical work in Archie should focus on real system operations
  Archie already owns rather than on a generic settings shell.
- Power and power-adjacent peripherals form the first GUI problem space.
- The backup-GUI track remains under this epic until the implementation
  boundary between Archie and `borg-automated-backups` is decided.
- Monitor output enable and disable behavior is split into a focused Waybar
  widget work item with confirmation and rollback requirements.
- Lid close policy is split into a focused work item backed by the `archie
  system` CLI because it changes privileged logind policy rather than monitor
  layout.
- The delivered GTK control window and tray applet are tracked retroactively as
  the first concrete desktop surface for the Archie system controls.
- Waybar theme and power profile controls are tracked separately because they
  add managed assets and CLI state transitions that can be reused outside the
  GUI.

## Main Quests

- Define the first-stage power and peripherals control GUI.
- Define the backup GUI scope, ownership boundary, and safety model.
- Build a monitor output widget that gives Archie a safe first graphical
  display-control surface.
- Build a lid close policy control that exposes Archie’s hibernate and
  OLED-safe screen-off-then-lock mode.
- Build the GTK desktop controls and tray applet for Archie-owned system
  settings.
- Add managed Waybar theme switching and power profile controls.

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
- system-gui-03
- system-gui-04
- system-gui-05
- system-gui-06
