# Fix Waybar Live And Share Indicators

Separate Archie’s Waybar session indicators so screen sharing is labeled as
sharing, and live or recording activity is detected from an explicit source
instead of PipeWire’s generic live-stream property.

## Status

In Progress

## Outcome

Waybar clearly tells the user when the desktop is being shared and when a real
live or recording workflow is active. The existing `LIVE` indicator no longer
fires just because `xdg-desktop-portal-hyprland` has an active PipeWire stream,
and a dedicated `SHARE` indicator appears while screen sharing is active.

## Decision Changes

- `stream.is-live` in PipeWire is not a user-facing broadcast signal; it should
  not be used as the source of truth for the `LIVE` label.
- Screen sharing should be detected as its own Waybar module by looking for
  active portal capture nodes from `xdg-desktop-portal-hyprland`.
- The `LIVE` indicator should remain available, but only when backed by an
  explicit live or recording signal such as OBS state, a supported recorder, or
  another concrete process-level source chosen during implementation.
- Indicator scripts should live under the managed Waybar or Hypr script assets
  instead of embedding complex `pw-dump | jq` expressions directly in every
  theme config.
- All managed Waybar themes should expose the same indicator semantics, even if
  their visual styling differs.

## Scope Notes

Included:

- Replace the current `custom/screenshare_detector` behavior that prints
  `LIVE` for portal screen capture streams.
- Add a `SHARE` indicator for active screen sharing through
  `xdg-desktop-portal-hyprland`.
- Repair or redesign the `LIVE` indicator so it reports only intentional live or
  recording activity.
- Update the default Waybar config and bundled themes that include the current
  detector.
- Add small shell helpers when that keeps Waybar JSON readable and behavior
  testable.

Not included:

- Building a full privacy dashboard.
- Adding historical logging of capture, sharing, recording, or broadcast
  activity.
- Supporting non-Hyprland portals unless the implementation can do so without
  broadening the design.

## Main Quests

- Audit the existing Waybar detector in the default config and managed themes,
  including `cjbassi`, `mechabar`, and `tokyonight`.
- Create a dedicated share detector that emits a compact `SHARE` label only
  while an active `xdg-desktop-portal-hyprland` screen capture stream exists.
- Replace inline detector commands with an Archie-managed helper script if the
  detection requires more than a short, readable command.
- Define the concrete source of truth for the `LIVE` indicator and update the
  module so it does not confuse screen sharing with live or recording state.
- Style the `LIVE` and `SHARE` modules in each managed theme so simultaneous
  states remain readable in the right-side Waybar module group.
- Document any runtime dependencies, such as `pw-dump`, `jq`, OBS tooling, or
  recorder-specific commands, near the helper script or Waybar config.

## Acceptance Criteria

- Starting a Hyprland portal screen share shows `SHARE` in Waybar.
- Ending the screen share removes `SHARE` within the configured Waybar polling
  interval.
- Starting a screen share does not show `LIVE` unless a separate supported live
  or recording source is active.
- Starting and stopping the supported live or recording workflow toggles `LIVE`
  independently from `SHARE`.
- The default Waybar config and all bundled managed themes use the same
  detection semantics.
- Any new shell helper passes `shellcheck`.
- Restarting Waybar through `~/.config/hypr/scripts/launch-waybar.sh` loads the
  updated modules without JSON or CSS errors.

## Metadata

### id

system-gui-07
