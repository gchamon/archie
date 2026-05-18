# Build A Waybar Monitor Output Widget

Implement a compact Waybar control for turning Hyprland monitor outputs on and
off while protecting the session from accidental or unrecoverable display
changes.

## Status

Planned

## Outcome

Archie has a Waybar-facing monitor widget that can enable and disable connected
Hyprland outputs, preserves the previous monitor layout before every change,
and automatically rolls back unconfirmed changes after 10 seconds.

## Decision Changes

- Monitor output control should become a focused implementation work item under
  the `system-gui` epic rather than remaining only inside the broader power and
  peripherals design track.
- The first user-facing surface is Waybar, using a custom module backed by an
  Archie-owned helper script.
- The initial scope is logical Hyprland output enable and disable behavior, not
  DPMS blanking or temporary screen sleep.
- Every output-disabling action must have a confirmation path and an automatic
  rollback path so the user is not left with an unusable display layout.
- The widget should manage one output change at a time before introducing
  monitor profiles or multi-output presets.

## Scope Notes

Included:

- Add a Waybar custom module that exposes connected monitor output state.
- Add or define the Hyprland helper script contract needed to list, toggle,
  confirm, and roll back output changes.
- Use Hyprland JSON state as the source of truth for connected and enabled
  outputs.
- Prevent disabling the last usable output.
- Restore the previous monitor layout when confirmation is not received within
  10 seconds.

Not included:

- DPMS-only monitor blanking.
- Full display profile management.
- Long-term layout persistence beyond the rollback state needed for the active
  change.
- A standalone GUI outside Waybar.

## Main Quests

- Define the Waybar custom module behavior, including the displayed icon or
  text, tooltip content, refresh interval, and click action.
- Implement the helper script under `deployment-packages/config/hypr/scripts/`
  with commands or modes for:
  - listing monitor state in a Waybar-friendly format
  - selecting the target output to toggle
  - saving the current Hyprland monitor layout before applying a change
  - applying a single output enable or disable operation
  - asking for explicit confirmation and reverting after 10 seconds without it
- Decide the confirmation surface, preferring an existing Archie-compatible
  graphical prompt such as Rofi when available.
- Add safety checks so the helper refuses to disable the only enabled output,
  handles missing utilities clearly, and restores the saved layout after a
  failed Hyprland command.
- Wire the widget into Waybar without disrupting existing modules, colors, or
  arrow separators.
- Document the manual verification flow for confirmed changes, timed-out
  rollback, rejected last-output disable, and failure recovery.

## Acceptance Criteria

- Waybar exposes a monitor output widget that reports the current connected
  output state.
- The widget can start a flow to enable or disable one Hyprland output at a
  time.
- Disabling the last usable output is rejected before any layout change is
  applied.
- After a monitor layout change, Archie asks for confirmation and restores the
  previous layout if the user does not confirm within 10 seconds.
- If Hyprland rejects the requested change or the resulting state cannot be
  verified, the helper restores the previous layout and reports the failure.
- The implementation can be verified by restarting Waybar with
  `~/.config/hypr/scripts/launch-waybar.sh` and by checking monitor state with
  `hyprctl monitors`.

## Metadata

### id

system-gui-03
