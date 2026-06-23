# Build Desktop Controls And Tray Applet

Deliver Archie’s first graphical system control surface as a GTK application
with a tray applet entrypoint, backed by the same `archie system` and monitor
helpers used by the CLI.

## Status

Done

## Outcome

Archie exposes a first-party desktop control window for monitor toggles, lid
close behavior, notifications, KDE Connect, power profiles, Waybar themes, and
keyboard shortcut lookup. A StatusNotifier applet gives the session a persistent
entrypoint for opening the controls without going through a terminal.

## Decision Changes

- The first GUI implementation is a compact GTK control window rather than a
  broad desktop settings replacement.
- GUI actions call Archie-owned backend functions instead of duplicating system
  command behavior in the interface layer.
- The applet uses StatusNotifier and DBusMenu interfaces so Waybar-compatible
  tray hosts can expose the Archie entrypoint.
- Keyboard shortcut documentation is rendered from the existing Markdown guide
  so the GUI does not create a second shortcut source of truth.
- Monitor toggles stay in the GUI backend as a pragmatic first implementation;
  the separate Waybar monitor-output work item remains available for a safer
  rollback-focused widget.

## Scope Notes

Included:

- Add `archie gui` as the graphical controls entrypoint.
- Add `archie applet` as the StatusNotifier tray entrypoint.
- Package applet icons and GUI CSS with the Python package.
- Add monitor listing and toggle helpers for Hyprland outputs.
- Surface existing and new `archie system` settings through segmented GTK
  controls.
- Render searchable keyboard shortcut documentation in the GUI.

Not included:

- Replacing every desktop settings tool.
- Implementing the monitor-output rollback flow described in
  `system-gui-03`.
- Building a separate daemon for long-running system state synchronization.

## Main Quests

- Add a GTK application window for Archie controls.
- Add controls for lid close behavior, notifications, KDE Connect, power
  profile, Waybar theme, and monitor state.
- Add a message and confirmation area for command results and monitor changes.
- Add a keyboard shortcuts tab that reads the repository or installed Markdown
  documentation.
- Add a StatusNotifier applet with an Open Controls action and a Quit action.
- Package the GUI and applet assets through the Python project metadata.
- Add tests for the CLI command tree and monitor helper behavior where the
  logic can be exercised without a live Hyprland session.

## Acceptance Criteria

- `archie gui` opens the Archie controls window in a graphical session.
- `archie applet` registers a tray item that can open the controls window.
- The GUI can read and set supported Archie system settings through the shared
  backend.
- The GUI can list and toggle Hyprland monitor outputs through Archie monitor
  helpers.
- Keyboard shortcuts are searchable from the GUI using the existing user guide
  content.
- Packaged installs include the applet icons, GUI stylesheet, and CLI
  entrypoints needed by the desktop controls.

## Metadata

### id

system-gui-05
