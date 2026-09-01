# Add Shy Mode Notification Privacy

Add a manual Archie privacy automation that keeps desktop notifications out of
an active screen share, then gives the user time to review what was missed when
sharing ends.

## Status

doing

## Outcome

Archie can enable shy mode from the CLI, GTK controls, or tray applet. While
shy mode is enabled, an active `SHARE` state pauses Dunst if it was not already
paused. When the share ends, Archie resumes Dunst and redisplays the missed
notifications one at a time. The tray applet visibly and textually reports
pending notifications without exposing their content during the share.

## Decision Changes

- Shy mode is a manual automation switch, not a second meaning of the existing
  notifications on/off control. It stays enabled after a share so it can guard
  the next share session.
- The existing `SHARE` detection contract is the source of truth for both
  Waybar and shy mode. Extract a shared Archie helper if that is necessary to
  prevent their results diverging.
- Archie pauses Dunst only when shy mode owns the transition. If Dunst was
  already paused when sharing starts, it remains paused and no automatic replay
  happens when sharing ends.
- The default replay is the newest ten missed notifications, displayed at
  five-second intervals. `archie system set shy-mode on` accepts options to
  configure both values; the GTK and applet controls use those defaults.
- Replay uses Dunst's native `dunstctl history-pop` behavior and is naturally
  bounded by the history Dunst retains.
- Store the enabled state and replay options in the shared Archie SQLite store
  so the CLI, GUI, and applet share the same persistent source of truth across
  user and root execution contexts.
- The applet uses an orange lower-right circular badge, approximately 30% of
  the logo height, only once shy-managed sharing has suppressed one or more
  notifications. Clear it after replay. Use tooltip and menu text to convey
  the same state without relying on color.
- Package matching green, red, yellow, and blue badge icon variants for future
  status states; only orange has behavior in this work item.

## Scope Notes

Included:

- Add `archie system get shy-mode` and `archie system set shy-mode on|off`.
- Add replay-count and replay-interval options to the `on` command, with
  validation that limits replay to Dunst's available history.
- Add a shy-mode toggle to the GTK controls and a checked `Shy mode` item to
  the applet's DBusMenu.
- Make the long-running applet monitor shy state, `SHARE`, Dunst pause
  ownership, missed-notification presence, and replay completion.
- Add and package the five applet badge assets.

Not included:

- Replacing Dunst's own history browser or storing notification content in
  Archie.
- Replaying notifications after a share that began while Dunst was manually
  paused.
- Adding further color-coded applet behaviors beyond the orange pending badge.

## Main Quests

- Create a small shy-mode settings and lifecycle layer in the Archie system
  backend. It must persist the CLI settings, distinguish Archie-owned pauses
  from existing pauses, and expose the current mode to UI consumers.
- Reuse the managed share detector from `system-gui-07` to react to share start
  and end. On share end, invoke up to the configured number of native Dunst
  history recalls at the configured interval, stopping safely when history is
  exhausted or the mode is disabled.
- Extend the GTK notification controls with shy-mode state and clear status
  feedback. Keep direct Dunst on/off controls available and do not let them
  silently claim ownership of a shy-managed pause.
- Extend the StatusNotifier applet with a checked shy-mode menu action,
  live tooltip status, periodic state refresh, and property-change signals so
  tray hosts promptly receive the base or badged icon.
- Produce and package the base-logo badge variants with consistent badge size,
  lower-right placement, and sufficient contrast against the logo.
- Cover backend state transitions and UI-facing formatting with tests that do
  not require a graphical session or a live Dunst instance.

## Acceptance Criteria

- `archie system get shy-mode` reports whether shy mode is enabled and its
  configured replay behavior; `set shy-mode on|off` changes the persisted
  setting.
- With shy mode enabled, beginning a `SHARE` pauses an otherwise active Dunst;
  ending it resumes Dunst and recalls at most the configured newest
  notifications at the configured interval.
- If Dunst was already paused at share start, shy mode neither resumes it nor
  recalls history at share end.
- The GUI and applet can change shy mode and reflect its current state.
- The applet shows the orange pending badge only when shy-managed sharing has
  missed notifications, clears it after replay, and reports the state in text.
- Orange, green, red, yellow, and blue lower-right badge variants are included
  in the installed package.
- Backend tests cover configuration, pause ownership, share transitions,
  replay bounds and timing, empty or failing Dunst history, and icon/menu
  state selection.

## Metadata

### id

system-gui-08
