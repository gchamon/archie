# Agent Guide - Arch Linux System Configuration (Archie)

<!--toc:start-->

- [Agent Guide - Arch Linux System Configuration (Archie)](#agent-guide-arch-linux-system-configuration-archie)
  - [1. Commands](#1-commands)
    - [Configuration Deployment & Verification](#configuration-deployment-verification)
    - [Linting & Validation](#linting-validation)
    - [Test Execution](#test-execution)
    - [Changelog Maintenance](#changelog-maintenance)
  - [2. Code Style Guidelines](#2-code-style-guidelines)
    - [General](#general)
    - [Shell Scripts (`bash`)](#shell-scripts-bash)
    - [Neovim (Lua)](#neovim-lua)
    - [Hyprland Configuration](#hyprland-configuration)
    - [Zsh Configuration](#zsh-configuration)
  - [3. Project Structure & Key Files](#3-project-structure-key-files)
  - [4. Detailed Component Guidance](#4-detailed-component-guidance)
    - [Neovim LSP & Plugins](#neovim-lsp-plugins)
    - [UI Customization (Waybar & Rofi)](#ui-customization-waybar-rofi)
    - [Git & Development](#git-development)
  - [5. Maintenance Workflow](#5-maintenance-workflow)
  - [6. Environment & Tooling](#6-environment-tooling)
  - [7. Common Agent Tasks](#7-common-agent-tasks)
    - [Adding a New Keybinding](#adding-a-new-keybinding)
    - [Creating a New Utility Script](#creating-a-new-utility-script)
    - [Updating Neovim LSP](#updating-neovim-lsp)
    - [Modifying Waybar](#modifying-waybar)
  - [8. Troubleshooting for Agents](#8-troubleshooting-for-agents)
  - [9. External Resources & Rules](#9-external-resources-rules)
  - [10. Rules of engagement](#10-rules-of-engagement)
    - [Restrictions](#restrictions)
    - [Preparation phase](#preparation-phase)
    - [Execution phase](#execution-phase)
    - [Post phase](#post-phase)
<!--toc:end-->

This repository contains the complete configuration for "Archie", a Hyprland-based Arch Linux desktop environment.

## 1. Commands

### Configuration Deployment & Verification

- **Deploy Home Package**: `stow --dir deployment-packages --target "$HOME" home`
- **Deploy Config Package**: `stow --dir deployment-packages --target "$HOME/.config" config`
- **Deploy Local Package**: `stow --dir deployment-packages --target "$HOME/.local" local`
- **Deploy `/etc` Package**: `sudo stow --dir deployment-packages --target /etc etc`
- **Deploy XKB Package**: `sudo stow --dir deployment-packages --target /usr/share/xkeyboard-config-2 xkb`
- **Reload Hyprland**: `hyprctl reload` (apply changes to `hyprland.conf` or sourced files)
- **Get Monitor Info**: `hyprctl monitors` (useful for configuring `device.conf`)
- **Get Workspace Info**: `hyprctl workspaces`
- **Check Backlight**: `brightnessctl -l`
- **List Explicit Packages**: `yay -Qe` (synchronized hourly to `/etc/pkglist.txt` via cron)

### Linting & Validation

- **Shell Scripts**: `shellcheck <path/to/script.sh>`
- **Neovim Health**: `:checkhealth` (inside nvim)
- **Neovim Plugins**: `:Lazy sync` (install/update plugins)
- **Waybar Config**: `waybar` (run from terminal to see error output)

### Test Execution

There are no formal unit tests in this repository. Verification is performed by reloading the respective service:

- **Hyprland**: `hyprctl reload`
- **Waybar**: Kill and restart (handled by `hypr/scripts/launch-waybar.sh`)
- **Zsh**: `source ~/.zshrc`

### Changelog Maintenance

- **Changelog File**: `CHANGELOG.md`
- **Standard**: Follow [common-changelog.org](https://common-changelog.org/)
- **Release Order**: Keep stable releases only, sorted latest-first, with headings in the form `## [x.y.z] - YYYY-MM-DD`
- **Version Links**: Link each release heading to the matching GitLab tag page using reference-style links
- **Change Groups**: Use only `Changed`, `Added`, `Removed`, and `Fixed`, in that order
- **Change Entries**: Write one-line, imperative, self-contained bullets and include Markdown links to the most relevant commit, merge request, or issue
- **Unreleased Changes**: Do not keep an `Unreleased` section
- **Before Tagging**: Update the changelog entry for the release before creating the git tag
- **Deriving Entries**: Start from `git log --reverse --oneline --no-merges <previous-tag>..<new-tag>`, then curate for user-visible changes instead of copying commit subjects verbatim
- **Major Upgrades**: Add a one-sentence notice after the release heading when readers must consult a migration or upgrade document

## 2. Code Style Guidelines

### General

- **Indentation**:
  - 4 spaces for Shell scripts, JS, TS, and VimScript.
  - 2 spaces for Lua and YAML.
- **File Naming**:
  - Kebab-case for scripts (`launch-waybar.sh`) and config files.
  - Distribution templates use `.dist` suffix (`device.dist.conf`).
- **Pathing**: Always use `$HOME` or `~` instead of hardcoded paths when referring to user directories.

### Shell Scripts (`bash`)

- **Shebang**: Always use `#!/bin/bash`.
- **Safety Flags**: Use `set -euo pipefail` at the start of complex scripts to ensure they fail early on errors or unset variables.
- **Conditionals**: Use the modern `[[ ... ]]` syntax instead of `[ ... ]`.
- **Variable Quoting**: Always quote variables (e.g., `"$VAR"`) unless word splitting is explicitly intended.
- **Subshells**: Use `$(command)` instead of backticks.
- **Math**: Use `bc` for floating point or complex math, and `(( ... ))` for simple integer arithmetic.
- **JSON Processing**: Use `jq` for any JSON output from system tools like `hyprctl`.
- **Functions**: Use `snake_case` for function names. Define local variables with `local`.

### Neovim (Lua)

- **LazyVim Conventions**: Adhere to the structure defined in `nvim/CLAUDE.md`.
- **Plugin Specs**: Return a table from files in `lua/plugins/*.lua`.
- **Global `vim`**: Use the `vim` global for all Neovim API calls.
- **Configuration Style**: Prefer explicit declarations over loops or other flow control for static Neovim configuration in `nvim/` when the expanded form stays readable.
- **Formatting**: Use `ruff` for Python and `stylua` for Lua (if available via Mason).
- **Indentation**: 2 spaces for Lua, but respect `ftplugin` overrides (e.g., 4 spaces for Shell/JS).

### Hyprland Configuration

- **Modularization**: Keep `hyprland.conf` clean by sourcing specific components using the `source = ~/.config/hypr/config/filename.conf` syntax.
- **Device-Specifics**: Never commit changes to `hypr/config/device.conf`. Modify `hypr/config/device.dist.conf` if adding new template variables.
- **Keybindings**: Follow the established `$mainMod` (SUPER) convention. Use `bindm` for mouse actions and `binde` for repeating keys (like volume/brightness).
- **Window Rules**: Use `windowrulev2` for modern window management.

### Zsh Configuration

- **Sourcing**: Custom shell logic lives under `deployment-packages/local/lib/zsh/` and is sourced from `.zshrc`.
- **Aliases and Functions**: Prefer adding shell helpers to the appropriate module under `deployment-packages/local/lib/zsh/commands-*.sh` and keep `commands.sh` as the loader only.
- **Completion**: Use the built-in `zsh` completion system (`compinit`).
- **Prompt**: Powerlevel10k is configured via `.p10k.zsh`.

## 3. Project Structure & Key Files

- `hypr/`: Hyprland compositor settings.
  - `hyprland.conf`: Main entry point.
  - `config/`: Sourced modular configs (keybinds, window rules, etc.).
  - `scripts/`: Helper scripts for session management and UI.
- `deployment-packages/`: GNU Stow packages that deploy Archie into the target roots.
  - `home/`: Files deployed directly under `$HOME`, including `.zshrc` and `.p10k-portable.zsh`.
  - `p10k-*/`: Optional prompt packages that each deploy `~/.p10k.zsh`.
  - `config/`: XDG config deployed under `$HOME/.config`.
  - `local/`: Shell library deployed under `$HOME/.local/lib/zsh`.
  - `etc/`: System files deployed under `/etc`.
  - `xkb/`: Active keyboard overrides deployed under `/usr/share/xkeyboard-config-2`.
- `nvim/`: LazyVim-based Neovim configuration.
  - `lua/config/`: options, keymaps, autocmds.
  - `lua/plugins/`: Plugin specifications.
  - `ftplugin/`: Language-specific overrides.
- `waybar/`: Status bar CSS and JSON configuration.

## 4. Detailed Component Guidance

### Neovim LSP & Plugins

- **LSP Management**: Handled by `lazy-lsp.nvim`. Preferred servers are mapped in `lua/plugins/lazy-lsp.lua`.
- **Python**: Uses `ruff` for linting/formatting and `pyright` for types.
- **Elixir**: Specialized setup in `lua/plugins/elixir-tools.lua`.
- **Adding Plugins**: Create a new file in `lua/plugins/` returning a table. Avoid modifying `lua/config/lazy.lua` unless changing bootstrap logic.

### UI Customization (Waybar & Rofi)

- **Waybar**: Modules are defined in `waybar/config`. CSS styling is in `waybar/style.css`. Always check if a new module requires a background script in `hypr/scripts/`.
- **Rofi**: Themes should be consistent with the system's color palette (often Catppuccin or similar).

### Git & Development

- **Git Strategy**: Default merge strategy is `merge` (rebase=false).
- **Signing**: Commits should be signed using SSH keys as per `docs/user/DEVELOPMENT.md`.
- **Dependencies**: Use `yay` for all package management. Prefer `nix` (single-user) for development tools to avoid permission issues in Neovim.

## 5. Maintenance Workflow

When modifying configurations:

1. **Read** the corresponding `.dist` or main config file first.
2. **Verify** dependencies (e.g., checking if a tool like `rofi` or `waybar` is configured).
3. **Apply** changes in the Stow package that owns the deployed path.
4. **Test** by reloading the service (e.g., `hyprctl reload`) or re-running the relevant `stow` command when checking deployment docs.
5. **Audit** shell scripts with `shellcheck`.

When preparing a release:

1. **Review** the commits since the previous tag with `git log --reverse --oneline --no-merges <previous-tag>..<new-tag>`.
2. **Curate** `CHANGELOG.md` using Common Changelog categories and GitLab references.
3. **Link** the release heading to the corresponding GitLab tag page and add any required migration notice.
4. **Commit** the changelog update before creating the new tag.

## 6. Environment & Tooling

- **Shell**: Zsh with Powerlevel10k.
- **Terminal**: Kitty (config in `.config/kitty/`).
- **Launcher**: Rofi (Wayland fork).
- **Notifications**: Dunst.
- **Clipboard**: `cliphist` with `wl-clipboard`.
- **Backups**: Managed via Borg (see `docs/BACKUP_AND_RESTORE.md`).
- **Package Sync**: Cron job syncs explicit packages to `/etc/pkglist.txt` hourly.

## 7. Common Agent Tasks

### Adding a New Keybinding

1. Identify the relevant config file in `hypr/config/` (usually `keybinds.conf`).
2. Follow the `$mainMod, <key>, <action>, <args>` pattern.
3. For multimedia keys, use the `XF86` names (e.g., `XF86AudioRaiseVolume`).
4. Test with `hyprctl reload`.

### Creating a New Utility Script

1. Place the script in `deployment-packages/config/hypr/scripts/` or `deployment-packages/local/lib/zsh/`, depending on whether it is a Hyprland helper or shell logic.
2. Ensure it has `#!/bin/bash` and `set -euo pipefail`.
3. Make it executable: `chmod +x <script>`.
4. If it's a UI script, consider using `rofi` for interaction.
5. Audit with `shellcheck`.

### Updating Neovim LSP

1. Modify `lua/plugins/lazy-lsp.lua` or `lua/plugins/lspconfig.lua`.
2. If adding a new language, check if it needs a specific `ftplugin` for indentation.
3. Run `:Lazy sync` and `:checkhealth` inside Neovim to verify.

### Modifying Waybar

1. Add/modify modules in `waybar/config`.
2. Update styles in `waybar/style.css`.
3. Restart Waybar using `hypr/scripts/launch-waybar.sh` (or let it auto-reload if `inotifywait` is running).

## 8. Troubleshooting for Agents

- **Hyprland crashes**: Check `~/.local/state/hypr/` for logs.
- **Waybar not showing**: Run `waybar` manually in a terminal to see CSS or JSON errors.
- **Script permission denied**: Verify `chmod +x` was applied.
- **LSP not starting**: Check `:LspInfo` and `:checkhealth lsp`.

## 9. External Resources & Rules

- **Neovim**: Refer to `nvim/CLAUDE.md` for plugin-specific architecture.
- **Hyprland Wiki**: [https://wiki.hyprland.org/](https://wiki.hyprland.org/)
- **Arch Wiki**: The primary source of truth for system-level packages.

## 10. Rules of engagement

This section provides instructions for how to behave when engaging with the
implementation of work item tasks.

These rules are engaged when starting a session with `engage with
{docs/work-items/[work-item-name].md}` or similar, where the
`[work-item-name]` pattern is documented in [the work items readme](./docs/work-items/README.md).

Archie aligns `epics` with GitLab epics and uses `work items` for these staged
planning documents. Reserve `milestone` for GitLab's timebox and release
tracking concept.

### Restrictions

- Never update a work item that is already completed

### Preparation phase

First always use the start of the session to ground yourself in the context of
the work item. You are free to pull data from ~/.codex/sessions/ whenever
necessary, but always ask when doing so because this can be token-intensive.

### Execution phase

The execution phase will go on until the user is satisfied with reviewing the
changes, before then the agent and the user are going to iterate on the
implementation.

It's important to always consider if there is need for a final pass over the
work item's acceptance criteria before exiting the Execution phase to catch
anything that was overlooked.

### Post phase

In the post phase of implementing a work item, propagate changes in the design and
decisions to the next work item in the sequence, if there are any, in which
case these changes have to be added to the last work item under `Decision
changes` section.

Never mark a work item as completed without first checking that all of its main
quests, side-quests that were taken on as part of the implementation, and exit
criteria were actually fulfilled. If any accepted quest or exit criterion is
still open, do not mark the work item as complete; leave it in an appropriate
non-complete status and record the remaining work explicitly.
