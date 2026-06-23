# Build A Lid Close Policy Backend

Expose Archie-owned lid close behavior through the `archie system` CLI and
Hyprland lid switch hook, leaving a stable backend contract for a future system
GUI control.

## Status

Done

## Outcome

Archie can switch between hibernate-on-lid-close and OLED-safe
screen-off-then-lock behavior, or disable lid close handling, through a
first-party CLI. Hyprland consumes the same setting through lid close/open
hooks, locks before hibernate, blanks displays on lid close before locking
after reopening in `lock` mode, and no-ops in `none` mode.

## Decision Changes

- Lid close policy belongs in the `system-gui` epic because it is a
  power-adjacent system operation Archie already owns, even though the first
  implementation surface is CLI-backed.
- The backend contract is setting-specific CLI commands:
  `archie system get lid-close-behavior` and
  `archie system set lid-close-behavior hibernate|lock`.
- The user-facing `hibernate` mode preserves Archie’s current systemd
  `hybrid-sleep` logind policy.
- The user-facing `lock` mode makes logind ignore lid close events and lets the
  Hyprland session turn displays off on close and lock after reopening.
- The user-facing `none` mode makes logind ignore lid close events and leaves
  Hyprland lid hooks as no-ops.
- The Hyprland helper logs close/open handling to `/tmp/handle-lid-event.log`
  so lid switch and DPMS behavior can be diagnosed from a real session.
- This work should remain separate from the monitor output widget because lid
  policy does not need monitor-layout rollback.
- The eventual GUI should call the CLI instead of reimplementing privileged
  logind file management.

## Scope Notes

Included:

- Add `archie system get lid-close-behavior`.
- Add `archie system set lid-close-behavior hibernate|lock|none`.
- Update Hyprland lid switch handling to consume the managed setting.
- Document the CLI behavior and manual verification path.

Not included:

- Replacing `systemd-logind` as the source of ACPI lid policy.
- Changing the monitor output enable/disable rollback flow.
- Building the graphical control; that can be layered on this CLI contract.

## Main Quests

- Add setting-specific `archie system get` and `archie system set` commands for
  lid close behavior.
- Detect the current managed lid close mode from the logind drop-in.
- Write the managed logind drop-in for `hibernate` and `lock` modes and reload
  `systemd-logind` when active.
- Replace the placeholder lid switch helper with close/open handling that
  turns DPMS off on close and locks after turning DPMS back on after reopening.
- Lock before logind-driven hibernate so resume prompts for a password.
- Document that `lock` mode depends on a running Hyprland session to blank the
  display and then lock after reopening.
- Add top-level `archie --help-all` output so nested CLI commands remain
  discoverable as the command tree grows.

## Acceptance Criteria

- `archie system get lid-close-behavior` prints the current managed behavior.
- `archie system set lid-close-behavior hibernate|lock` writes the matching
  logind policy and reloads logind when active.
- `archie system set lid-close-behavior none` disables Archie lid close actions
  while keeping logind configured to ignore lid switches.
- `archie system set lid-close-behavior --help` shows only lid-specific values.
- `archie --help-all` prints the nested CLI command hierarchy.
- Hyprland lid close/open events call Archie’s lid helper, which turns DPMS off
  on close and locks after turning DPMS back on after reopening.
- Hyprland lid close events in `hibernate` mode start `hyprlock` before logind
  puts the machine to sleep.
- User documentation explains the `hibernate` to `hybrid-sleep` mapping and the
  Hyprland dependency of `lock` mode.

## Metadata

### id

system-gui-04
