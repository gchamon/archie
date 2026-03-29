# Changelog

<!--toc:start-->

- [Changelog](#changelog)
  - [[2.0] - 2025-11-03](#20-2025-11-03)
    - [Changed](#changed)
    - [Added](#added)
    - [Fixed](#fixed)
  - [[1.2] - 2025-06-30](#12-2025-06-30)
    - [Changed](#changed-1)
    - [Added](#added-1)
    - [Fixed](#fixed-1)
  - [[1.1] - 2025-06-12](#11-2025-06-12)
    - [Changed](#changed-2)
    - [Added](#added-2)
  - [[1.0] - 2025-06-12](#10-2025-06-12)
<!--toc:end-->

## [2.0] - 2025-11-03

_If you are upgrading: please see [docs/user/MIGRATING.md](docs/user/MIGRATING.md)._

### Changed

- Reorganize Archie into GNU Stow deployment packages and refactor the repository layout ([`16750c2`](https://gitlab.com/gabriel.chamon/archie/-/commit/16750c2))
- Change device-specific Hyprland handling to better isolate host-dependent configuration ([`78b76a1`](https://gitlab.com/gabriel.chamon/archie/-/commit/78b76a1), [`2d0ea26`](https://gitlab.com/gabriel.chamon/archie/-/commit/2d0ea26))
- Expand development tooling documentation and shell integrations for daily work ([`bdd0efa`](https://gitlab.com/gabriel.chamon/archie/-/commit/bdd0efa), [`28f0558`](https://gitlab.com/gabriel.chamon/archie/-/commit/28f0558))

### Added

- Add Terraform and Neovim LSP improvements, including Terraform tooling, folder-based exclusions, and JavaScript and TypeScript indentation overrides ([`49e253d`](https://gitlab.com/gabriel.chamon/archie/-/commit/49e253d), [`e53634b`](https://gitlab.com/gabriel.chamon/archie/-/commit/e53634b), [`52239f4`](https://gitlab.com/gabriel.chamon/archie/-/commit/52239f4))
- Add laptop-oriented power and display configuration, including hibernate-on-lid-close and Yoga-specific Hyprshade presets ([`5af1579`](https://gitlab.com/gabriel.chamon/archie/-/commit/5af1579), [`08e27d6`](https://gitlab.com/gabriel.chamon/archie/-/commit/08e27d6))
- Add desktop workflow improvements such as pamixer, ranger, rofi-driven dunst actions, and safer screenshot handling around `ksnip` ([`122fde9`](https://gitlab.com/gabriel.chamon/archie/-/commit/122fde9), [`158c641`](https://gitlab.com/gabriel.chamon/archie/-/commit/158c641), [`d48a9b6`](https://gitlab.com/gabriel.chamon/archie/-/commit/d48a9b6), [`66bc7db`](https://gitlab.com/gabriel.chamon/archie/-/commit/66bc7db))

### Fixed

- Fix NVIDIA dual-monitor support after upstream configuration changes ([`520f82c`](https://gitlab.com/gabriel.chamon/archie/-/commit/520f82c))
- Fix screenshot capture compatibility by removing the unsupported `--cursor` flag from the grimblast flow ([`f8d763f`](https://gitlab.com/gabriel.chamon/archie/-/commit/f8d763f))

## [1.2] - 2025-06-30

### Changed

- Parameterize Hyprland backlight handling through a device-specific `$backlightDevice` setting and document the new override point ([`e5f9695`](https://gitlab.com/gabriel.chamon/archie/-/commit/e5f9695), [`4e69f45`](https://gitlab.com/gabriel.chamon/archie/-/commit/4e69f45), [`39f81f5`](https://gitlab.com/gabriel.chamon/archie/-/commit/39f81f5))
- Expand backup and restore documentation and include `makepkg.conf` in the restored `/etc` set ([`19d7024`](https://gitlab.com/gabriel.chamon/archie/-/commit/19d7024), [`d426065`](https://gitlab.com/gabriel.chamon/archie/-/commit/d426065))

### Added

- Add XKB keyboard customizations and a human-readable keyboard shortcuts guide ([`e08f991`](https://gitlab.com/gabriel.chamon/archie/-/commit/e08f991), [`12a7b3b`](https://gitlab.com/gabriel.chamon/archie/-/commit/12a7b3b))
- Add brightness control dependencies and keybinding support for laptop displays ([`2026e8d`](https://gitlab.com/gabriel.chamon/archie/-/commit/2026e8d))
- Add Elixir editor support with Treesitter and improved LSP configuration ([`7c63aae`](https://gitlab.com/gabriel.chamon/archie/-/commit/7c63aae), [`e618ac1`](https://gitlab.com/gabriel.chamon/archie/-/commit/e618ac1))
- Add shell and package manager quality-of-life updates, including `fd`, `frece`, `lsp-toggle`, `zsh-completions`, and single-user `nix` setup guidance ([`f112789`](https://gitlab.com/gabriel.chamon/archie/-/commit/f112789), [`102fb06`](https://gitlab.com/gabriel.chamon/archie/-/commit/102fb06), [`36cc167`](https://gitlab.com/gabriel.chamon/archie/-/commit/36cc167), [`e32ee96`](https://gitlab.com/gabriel.chamon/archie/-/commit/e32ee96), [`8938850`](https://gitlab.com/gabriel.chamon/archie/-/commit/8938850))

### Fixed

- Fix active workspace highlighting and spacing inconsistencies in Waybar ([`c198771`](https://gitlab.com/gabriel.chamon/archie/-/commit/c198771), [`ab7631d`](https://gitlab.com/gabriel.chamon/archie/-/commit/ab7631d))

## [1.1] - 2025-06-12

### Changed

- Split package guidance into essential and development groups and clarify the LazyVim setup path ([`2057a04`](https://gitlab.com/gabriel.chamon/archie/-/commit/2057a04))

### Added

- Add containerization and virtualization setup documentation for Docker, QEMU, libvirt, and Incus ([`812ea22`](https://gitlab.com/gabriel.chamon/archie/-/commit/812ea22))

## [1.0] - 2025-06-12

_First release._

[2.0]: https://gitlab.com/gabriel.chamon/archie/-/tags/v2.0
[1.2]: https://gitlab.com/gabriel.chamon/archie/-/tags/v1.2
[1.1]: https://gitlab.com/gabriel.chamon/archie/-/tags/v1.1
[1.0]: https://gitlab.com/gabriel.chamon/archie/-/tags/v1.0
