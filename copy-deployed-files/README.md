# Copy-Deployed Files

This tree contains Archie-managed files that must be copied into their target
paths as real files instead of being deployed with GNU Stow symlinks.

Use this only when the target consumer cannot safely follow symlinks back into
the repository or when the file is intentionally mutated at runtime.

Paths under `etc/` are copied to their matching absolute paths under `/etc`.
`systemd-logind` is one such consumer: its service runs with
`ProtectHome=yes`, so logind drop-ins under `/etc/systemd/logind.conf.d/`
cannot be Stow symlinks pointing into `$HOME`.

Paths under `home/` are copied to matching paths under `$HOME`. Waybar's active
`config` and `style.css` live here because `archie system set waybar-theme`
rewrites `~/.config/waybar/config` and `~/.config/waybar/style.css`; keeping
those targets as real files prevents theme changes from modifying tracked Stow
package files.
