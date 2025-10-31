# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Neovim configuration based on [LazyVim](https://lazyvim.github.io/), a starter template that uses [lazy.nvim](https://github.com/folke/lazy.nvim) as its plugin manager. The configuration is structured following LazyVim's conventions with custom overrides and additional plugins.

## Architecture

### Plugin Management

- **Plugin Manager**: lazy.nvim (bootstrapped automatically in `lua/config/lazy.lua`)
- **Base Distribution**: LazyVim provides the foundation with sensible defaults
- **Custom Plugins**: Located in `lua/plugins/*.lua`, each file returns a table of plugin specifications
- **Plugin Loading**: Lazy-loading is disabled by default (`lazy = false` in lazy.nvim setup) for custom plugins

### Configuration Structure

```
~/.config/nvim/
├── init.lua                    # Entry point, loads config.lazy
├── lua/
│   ├── config/                 # Core configuration
│   │   ├── lazy.lua           # Plugin manager setup and lazy.nvim bootstrap
│   │   ├── options.lua        # Vim options (extends LazyVim defaults)
│   │   ├── keymaps.lua        # Custom keymaps (extends LazyVim defaults)
│   │   └── autocmds.lua       # Custom autocommands
│   └── plugins/               # Plugin specifications
│       ├── lspconfig.lua      # LSP base configuration
│       ├── lazy-lsp.lua       # Automatic LSP server setup
│       ├── elixir-tools.lua   # Elixir language support
│       ├── terraform.lua      # Terraform/HCL support
│       ├── treesitter.lua     # Syntax highlighting config
│       ├── colorscheme.lua    # Color scheme (lunar theme)
│       └── snacks.nvim        # File picker configuration
└── ftplugin/                  # Filetype-specific settings
    ├── sh.lua / bash.lua      # Shell: 4-space tabs
    └── javascript.vim / typescript.vim  # JS/TS: 4-space tabs with expandtab
```

### LSP Configuration Architecture

This configuration uses a multi-layered LSP setup:

1. **lazy-lsp.nvim** (`lua/plugins/lazy-lsp.lua`): Automatically installs and configures LSP servers based on Mason registry
   - Excluded servers list prevents unwanted LSP installations
   - Preferred servers map defines which LSP to use per filetype
   - Python uses both `ruff` (linter/formatter) and `pyright` (type checker)
   - Markdown has no LSP configured (empty array)

2. **nvim-lspconfig** (`lua/plugins/lspconfig.lua`): Manual LSP server configuration
   - `bashls` configured for sh and zsh filetypes
   - Format notifications enabled for debugging
   - Inlay hints disabled globally

3. **lsp-toggle.nvim**: Provides commands to toggle LSP servers on/off per buffer

4. **Language-Specific Plugins**: Some languages bypass standard LSP config
   - **Elixir**: Uses `elixir-tools.nvim` which configures both `nextls` and `elixirls` directly
     - Custom keymaps: `<space>fp` (from pipe), `<space>tp` (to pipe), `<space>em` (expand macro)
   - **Terraform**: Configured via both treesitter and lspconfig with `terraformls`

### Treesitter Configuration

Treesitter parsers are configured in `lua/plugins/treesitter.lua`:
- Explicitly ensures Elixir-related parsers: eex, elixir, erlang, heex, html, surface
- Additional parsers (terraform, hcl) added via terraform.lua
- Uses master branch with `:TSUpdate` build command

### File Type Customizations

Located in `ftplugin/`:
- **Shell scripts** (sh/bash): 4-space indentation via Lua
- **JavaScript/TypeScript**: 4-space indentation with expanded tabs via VimScript

### Custom Autocommands

Defined in `lua/config/autocmds.lua`:
- GitLab CI files (`*.gitlab-ci*.{yml,yaml}`) are detected as `yaml.gitlab` filetype

## Working With This Configuration

### Adding New Plugins

Create a new file in `lua/plugins/` that returns a table:

```lua
return {
  {
    "username/plugin-name",
    opts = {
      -- configuration here
    },
  },
}
```

### Adding LSP Servers

**For standard LSP servers**:
- Add to `preferred_servers` table in `lua/plugins/lazy-lsp.lua`
- lazy-lsp will automatically install and configure via Mason

**For custom LSP configuration**:
- Add server config to `servers` table in `lua/plugins/lspconfig.lua`

**To prevent an LSP from auto-installing**:
- Add server name to `excluded_servers` list in `lua/plugins/lazy-lsp.lua`

### Modifying Filetype Settings

Either:
- Create/edit `ftplugin/{filetype}.lua` or `ftplugin/{filetype}.vim`
- Or add autocommand in `lua/config/autocmds.lua`

### Plugin Management Commands

LazyVim provides these commands (via lazy.nvim):
- `:Lazy` - Open plugin manager UI
- `:Lazy update` - Update all plugins
- `:Lazy sync` - Install missing and update existing plugins
- `:Lazy clean` - Remove unused plugins

### LSP Management Commands

- `:LspToggle` - Toggle LSP servers (from lsp-toggle.nvim)
- `:Mason` - Open Mason UI for LSP/formatter/linter management
- `:LspInfo` - Show LSP client status for current buffer

### Colorscheme

Currently using the `lunar` colorscheme (from LunarVim). To change:
- Modify `lua/plugins/colorscheme.lua`
- Update both the plugin spec and the `opts.colorscheme` value

## Key Configuration Details

- **Package Manager**: lazy.nvim with automatic bootstrap
- **Update Checking**: Enabled for plugins (notify disabled)
- **Elixir Support**: Comprehensive via elixir-tools.nvim with both nextls and elixirls
- **Dialyzer**: Disabled in elixirls config (performance optimization)
- **Test Lenses**: Disabled in elixirls config
- **Picker**: Snacks.nvim picker configured to show hidden and .gitignore files
- **Disabled RTP Plugins**: gzip, tarPlugin, tohtml, tutor, zipPlugin
