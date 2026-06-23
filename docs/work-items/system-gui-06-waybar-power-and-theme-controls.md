# Add Waybar Power And Theme Controls

Extend Archie’s Waybar integration so the bar can expose power profile state
and switch between managed theme layouts through Archie-owned commands.

## Status

Done

## Outcome

Archie can switch Waybar between managed themes, install those themes into the
user configuration, and expose power profile controls in both Waybar and the
desktop GUI. The CLI owns the state transition so graphical controls and shell
commands share one backend.

## Decision Changes

- Waybar themes are treated as managed Archie assets and copied into the live
  Waybar config through `archie system set waybar-theme`.
- The active theme is tracked in `~/.config/waybar/.archie-theme` so the GUI
  can report the current state without inferring it from generated config
  contents.
- Power profiles are exposed through `power-profiles-daemon` using
  `archie system get/set power-profile`.
- The install script should deploy bundled Waybar theme assets alongside the
  Python package so CLI theme switching works after installation.
- Existing Waybar configuration remains the default theme baseline while
  additional themes live under managed theme directories.

## Scope Notes

Included:

- Add `archie system get power-profile`.
- Add `archie system set power-profile performance|balanced|power-saver`.
- Add `archie system get waybar-theme`.
- Add `archie system set waybar-theme cjbassi|mechabar|tokyonight`.
- Add managed Waybar theme config and style assets.
- Wire power profile and theme controls into the GUI and Waybar-facing
  configuration.
- Ignore makepkg build outputs for the CLI packaging directory.

Not included:

- Building a visual theme editor.
- Persisting arbitrary third-party Waybar themes.
- Replacing `power-profiles-daemon` or adding battery analytics.

## Main Quests

- Add CLI-backed power profile detection and setting.
- Add CLI-backed Waybar theme detection and switching.
- Bundle the managed theme assets in source and deployed config locations.
- Update Waybar configuration and styling for the new control surface.
- Update installation and packaging metadata so the CLI and assets are
  available after package install.
- Keep generated makepkg archives and build directories out of the repository.

## Acceptance Criteria

- `archie system get power-profile` reports the active daemon profile.
- `archie system set power-profile performance|balanced|power-saver` changes
  the active profile through `powerprofilesctl`.
- `archie system get waybar-theme` reports the Archie-managed theme state.
- `archie system set waybar-theme cjbassi|mechabar|tokyonight` updates the
  live Waybar config and style paths.
- Waybar and the GUI expose controls for the same power profile and theme
  values.
- `packaging/archie-cli/.gitignore` prevents generated makepkg artifacts from
  being tracked.

## Metadata

### id

system-gui-06
