# Restructure The Repo For Deployment Management

Reorganize the repository so the deployment model from Work Item 1 is real and
executable.

## Status

Done.

## Decision Changes

This work item implements the deployment-management decisions accepted in
[Work Item 1](deployment-management-01-design.md).

- The package root is `deployment-packages/`.
- The base Stow packages are `home`, `config`, `local`, `etc`, and `xkb`.
- Terminal Powerlevel10k variants use separate Stow packages:
  `p10k-classic`, `p10k-lean`, `p10k-pure`, and `p10k-rainbow`.
- Package targets are `~`, `~/.config`, `~/.local`, `/etc`, and
  `/usr/share/xkeyboard-config-2`.
- Home-level deployment uses:
  `stow --dir deployment-packages --target "$HOME" home`.
- Theme deployment uses one optional package in addition to `home`, for
  example:
  `stow --dir deployment-packages --target "$HOME" p10k-lean`.
- XDG config deployment uses:
  `stow --dir deployment-packages --target "$HOME/.config" config`.
- Shell library deployment uses:
  `stow --dir deployment-packages --target "$HOME/.local" local`.
- System deployment uses direct `sudo stow` commands rather than a wrapper
  script.
- Runtime paths in deployed configs and scripts must remain unchanged, even
  after the repo is restructured.
- Files that remain outside Stow management include machine-specific files
  derived from templates such as `device.conf`, `hyprpaper.conf`, and
  `overrides.sh`.
- Migration from the old `rsync` deployment model uses backup-and-cleanup of
  conflicting files before running `stow`.
- XKB deployment keeps `/etc/xkb-customizations` as the stable source used by
  the pacman hook, while initial deployment also stows files into
  `/usr/share/xkeyboard-config-2`.

## Outcome

The repo can be cloned outside the target directories, deployed with Stow into
the intended home and system roots, and migrated from the old copied-file model
without changing the runtime paths expected by Archie.

## Scope Notes

This work item covers only the repository restructure needed to make the Stow
deployment model real.

Included:

- Moving tracked files into the final `deployment-packages/` layout.
- Making only the minimal config or script adjustments required to preserve the
  existing runtime paths after the move.
- Rehearsing and documenting the migration behavior from the old `rsync`
  deployment model at an implementation level.

Not included:

- Introducing a deployment wrapper script.
- Rewriting the user-facing deployment guides in full.
- Adding CI or automated deployment validation.

## Main Quests

### 1. Build the Stow package layout

Create `deployment-packages/` with these packages and targets:

- `home` targeting `$HOME`.
- `p10k-classic`, `p10k-lean`, `p10k-pure`, and `p10k-rainbow`, each
  targeting `$HOME`.
- `config` targeting `$HOME/.config`.
- `local` targeting `$HOME/.local`.
- `etc` targeting `/etc`.
- `xkb` targeting `/usr/share/xkeyboard-config-2`.

### 2. Move tracked files into the correct packages

Populate the packages with the current tracked content:

- `home` contains `.zshrc` and `.p10k-portable.zsh`.
- `p10k-classic`, `p10k-lean`, `p10k-pure`, and `p10k-rainbow` each contain
  exactly one terminal Powerlevel10k theme file deployed as `~/.p10k.zsh`.
- `config` contains the current XDG-style top-level directories:
  `hypr/`, `waybar/`, `nvim/`, `kitty/`, `dunst/`, `rofi/`, `k9s/`,
  `onedrive/`, and `lvim/`.
- `local` contains the tracked shell library files deployed under
  `~/.local/lib/zsh/`, including:
  `aliases.sh`, `commands-core.sh`, `commands-devtools.sh`,
  `commands-git.sh`, `commands-pacman.sh`, `commands-system.sh`,
  `commands.sh`, `functions.sh`, `overrides.dist.sh`, `README.md`, and a
  `.gitignore` that excludes the machine-specific `overrides.sh`.
- `etc` contains:
  - `cronjobs/cron.hourly/yay_pkglist` deployed as `/etc/cron.hourly/yay_pkglist`
  - the XKB pacman hook deployed as `/etc/pacman.d/hooks/00-xkb.hook`
  - the stable XKB source tree deployed as `/etc/xkb-customizations/...`
- `xkb` contains the tracked XKB symbol overrides currently under
  `xkb-customizations/us-br/symbols/us`.

### 3. Preserve runtime behavior

- Keep the deployed runtime paths unchanged for Hyprland, zsh, and all other
  Archie-managed tools after the repo move.
- Verify that hardcoded paths such as `~/.config/hypr/...` still resolve from
  the deployed locations.
- Add only the path-preserving adjustments required to keep the current configs
  and scripts working after the restructure.

### 4. Rehearse migration from the old deployment model

- Identify copied files from the old `rsync` deployment flow that would block
  `stow` and define the required backup, move-aside, or cleanup steps.
- Preserve unmanaged machine-specific files that remain outside Stow
  management, including `hypr/config/device.conf` and
  `hypr/hyprpaper.conf`.
- Rehearse the migration on a machine with a previous copied deployment and
  record the conflict classes that must be handled before `stow` succeeds.

## Manual Testing

This section is intended for a human tester validating the restructure on a
separate machine or environment. Use the commands below as the copy-paste entry
point for the manual test flow.

### Clean Deployment

Use this flow on a machine with no previous Archie deployment.

```bash
stow --dir deployment-packages --target "$HOME" home
stow --dir deployment-packages --target "$HOME/.config" config
stow --dir deployment-packages --target "$HOME/.local" local
sudo stow --dir deployment-packages --target /etc etc
sudo stow --dir deployment-packages --target /usr/share/xkeyboard-config-2 xkb
```

Test the terminal theme packages one at a time. Remove the currently selected
`p10k-*` package before deploying the next one so only one terminal theme is
active at a time.

```bash
stow --dir deployment-packages --target "$HOME" p10k-classic
stow --dir deployment-packages --target "$HOME" --delete p10k-classic
stow --dir deployment-packages --target "$HOME" p10k-lean
stow --dir deployment-packages --target "$HOME" --delete p10k-lean
stow --dir deployment-packages --target "$HOME" p10k-pure
stow --dir deployment-packages --target "$HOME" --delete p10k-pure
stow --dir deployment-packages --target "$HOME" p10k-rainbow
stow --dir deployment-packages --target "$HOME" --delete p10k-rainbow
```

### Migration Rehearsal

Use this flow on a machine previously deployed with the old `rsync` model.
Back up or move aside conflicting copied files before running `stow`.

Choose the terminal theme package you want to test during the migration
rehearsal, then run the full backup flow below. It moves aside conflicting
copied files for `home`, the selected `p10k-*` package, `config`, and `local`,
and it also covers `etc` and `xkb` when the environment being tested still
includes the old system-level copied deployment. The file lists are generated
from the package contents rather than hardcoded deployed paths so the
rehearsal stays aligned with the package layout.

```bash
SELECTED_P10K_PACKAGE="p10k-lean"
mkdir -p "$HOME/archie-pre-stow-backup"

backup_stow_conflicts() {
  local package_dir="$1"
  local deploy_root="$2"
  local backup_root="$3"

  fd '.' "$package_dir" --type f | while read -r file_to_deploy; do
    relative_path="${file_to_deploy#"$package_dir"/}"
    deployed_path="$deploy_root/$relative_path"
    backup_path="$backup_root/$relative_path"

    if [[ -e "$deployed_path" || -L "$deployed_path" ]]; then
      mkdir -p "$(dirname "$backup_path")"
      mv "$deployed_path" "$backup_path"
    fi
  done
}

backup_stow_conflicts_sudo() {
  local package_dir="$1"
  local deploy_root="$2"
  local backup_root="$3"

  sudo fd '.' "$package_dir" --type f | while read -r file_to_deploy; do
    relative_path="${file_to_deploy#"$package_dir"/}"
    deployed_path="$deploy_root/$relative_path"
    backup_path="$backup_root/$relative_path"

    if sudo test -e "$deployed_path" || sudo test -L "$deployed_path"; then
      sudo mkdir -p "$(dirname "$backup_path")"
      sudo mv "$deployed_path" "$backup_path"
    fi
  done
}

for package_name in home "$SELECTED_P10K_PACKAGE"; do
  backup_stow_conflicts \
    "deployment-packages/$package_name" \
    "$HOME" \
    "$HOME/archie-pre-stow-backup"
done

backup_stow_conflicts \
  "deployment-packages/config" \
  "$HOME/.config" \
  "$HOME/archie-pre-stow-backup/.config"

backup_stow_conflicts \
  "deployment-packages/local" \
  "$HOME/.local" \
  "$HOME/archie-pre-stow-backup/.local"

sudo mkdir -p /root/archie-pre-stow-backup

backup_stow_conflicts_sudo \
  "deployment-packages/etc" \
  "/etc" \
  "/root/archie-pre-stow-backup"

backup_stow_conflicts_sudo \
  "deployment-packages/xkb" \
  "/usr/share/xkeyboard-config-2" \
  "/root/archie-pre-stow-backup/usr-share-xkeyboard-config-2"
```

After the conflicting copied files have been moved aside, deploy the selected
packages into their target roots with `stow`:

```bash
stow --dir deployment-packages --target "$HOME" home
stow --dir deployment-packages --target "$HOME" "$SELECTED_P10K_PACKAGE"
stow --dir deployment-packages --target "$HOME/.config" config
stow --dir deployment-packages --target "$HOME/.local" local
sudo stow --dir deployment-packages --target /etc etc
sudo stow --dir deployment-packages --target /usr/share/xkeyboard-config-2 xkb
```

Preserve unmanaged machine-specific files outside Stow management during the
migration rehearsal, including `hypr/config/device.conf` and
`hypr/hyprpaper.conf`.

Record the conflict classes encountered during migration so the cleanup steps
are known before the documentation rewrite work item.

### Migration Rollback

If the migration rehearsal fails and leaves the environment in an inconsistent
state, first remove the Stow-managed links that were just created:

```bash
stow --dir deployment-packages --target "$HOME" --delete home
stow --dir deployment-packages --target "$HOME" --delete "$SELECTED_P10K_PACKAGE"
stow --dir deployment-packages --target "$HOME/.config" --delete config
stow --dir deployment-packages --target "$HOME/.local" --delete local
sudo stow --dir deployment-packages --target /etc --delete etc
sudo stow --dir deployment-packages --target /usr/share/xkeyboard-config-2 --delete xkb
```

Restore the backed-up home, XDG, and local library files:

```bash
fd '.' "$HOME/archie-pre-stow-backup" --type f | while read -r backup_file; do
  relative_path="${backup_file#"$HOME/archie-pre-stow-backup"/}"
  restore_path="$HOME/$relative_path"

  mkdir -p "$(dirname "$restore_path")"
  mv "$backup_file" "$restore_path"
done
```

If system-level files were backed up during the rehearsal, restore them as
well:

```bash
sudo fd '.' /root/archie-pre-stow-backup --type f | while read -r backup_file; do
  relative_path="${backup_file#/root/archie-pre-stow-backup/}"

  case "$relative_path" in
    usr-share-xkeyboard-config-2/*)
      restore_path="/usr/share/xkeyboard-config-2/${relative_path#usr-share-xkeyboard-config-2/}"
      ;;
    *)
      restore_path="/etc/$relative_path"
      ;;
  esac

  sudo mkdir -p "$(dirname "$restore_path")"
  sudo mv "$backup_file" "$restore_path"
done
```

### Verification

After deployment or migration rehearsal, confirm the following:

- Hyprland, zsh, and related scripts still resolve files from the expected
  deployed runtime paths under `~/.config/...`.
- The shell library files resolve from `~/.local/lib/zsh/...`, and zsh still
  finds `commands.sh`, `functions.sh`, and the other sourced files through the
  deployed path.
- Unmanaged template-derived files still follow the intended out-of-band setup
  flow.
- XKB still uses `/etc/xkb-customizations` as the stable source and
  `/usr/share/xkeyboard-config-2` as the active override target.
- Exactly one terminal Powerlevel10k theme package was selected in addition to
  `home`, and it deployed `~/.p10k.zsh`.

If command-line verification is useful in the test environment, use:

```bash
ls -l "$HOME/.zshrc" "$HOME/.p10k.zsh" "$HOME/.p10k-portable.zsh" "$HOME/.config/hypr"
ls -l "$HOME/.local/lib/zsh"
ls -l /etc/xkb-customizations /usr/share/xkeyboard-config-2/symbols/us
```

## Acceptance Criteria

- The repo contains the final `deployment-packages/` layout and package
  inventory described in this work item.
- `stow` can deploy `home`, `config`, `etc`, and `xkb` into the correct
  targets, can deploy `local` into `$HOME/.local`, and can deploy exactly one
  selected `p10k-*` theme package into `$HOME`.
- Existing Archie functionality still resolves files from the expected runtime
  paths, especially under `~/.config/...`.
- A clean-machine deployment path has been exercised manually.
- Migration from the old copied deployment method has been rehearsed manually,
  and the required conflict-cleanup steps are known.

## Metadata

### id

deployment-management-02
