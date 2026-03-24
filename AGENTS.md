# Agent Guide - Arch Linux System Configuration (Archie)

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
- **Formatting**: Use `ruff` for Python and `stylua` for Lua (if available via Mason).
- **Indentation**: 2 spaces for Lua, but respect `ftplugin` overrides (e.g., 4 spaces for Shell/JS).

### Hyprland Configuration

- **Modularization**: Keep `hyprland.conf` clean by sourcing specific components using the `source = ~/.config/hypr/config/filename.conf` syntax.
- **Device-Specifics**: Never commit changes to `hypr/config/device.conf`. Modify `hypr/config/device.dist.conf` if adding new template variables.
- **Keybindings**: Follow the established `$mainMod` (SUPER) convention. Use `bindm` for mouse actions and `binde` for repeating keys (like volume/brightness).
- **Window Rules**: Use `windowrulev2` for modern window management.

### Zsh Configuration

- **Sourcing**: Custom shell logic lives under `deployment-packages/local/lib/zsh/` and is sourced from `.zshrc`.
- **Aliases**: Prefer grouping aliases in `deployment-packages/local/lib/zsh/aliases.sh`.
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
- **Signing**: Commits should be signed using SSH keys as per `docs/DEVELOPMENT.md`.
- **Dependencies**: Use `yay` for all package management. Prefer `nix` (single-user) for development tools to avoid permission issues in Neovim.

## 5. Maintenance Workflow

When modifying configurations:

1. **Read** the corresponding `.dist` or main config file first.
2. **Verify** dependencies (e.g., checking if a tool like `rofi` or `waybar` is configured).
3. **Apply** changes in the Stow package that owns the deployed path.
4. **Test** by reloading the service (e.g., `hyprctl reload`) or re-running the relevant `stow` command when checking deployment docs.
5. **Audit** shell scripts with `shellcheck`.

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
implementation of milestone tasks.

These rules are engaged when starting a session with `engage with
{docs/milestone/[milestone-name].md}` or similar, where the `[milestone-name]`
pattern is documented in [the milestone readme](./docs/milestones/README.md).

### Preparation phase

First always use the start of the session to ground yourself in the context of
the milestone. You are free to pull data from ~/.codex/sessions/ whenever
necessary, but always ask when doing so because this can be token-intensive.

### Execution phase

The exeuction phase will go on until the user is satisfied with reviewing the
changes, before then the agent and the user are going to iterate on the
implementation.

It's important to always consider if there is need for a final pass over the
milestone's acceptance criteria before exiting the Execution phase to catch
anything that was overlooked.

### Post phase

In the post phase of implementing a milestone, propagate changes in the design and
decisions to the next milestone in the sequence, if there are any, in which
case these changes have to be added to the last milestone under `Decision
changes` section.
