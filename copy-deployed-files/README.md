# Copy-Deployed Files

This tree contains Archie-managed files that must be copied into their target
paths as real files instead of being deployed with GNU Stow symlinks.

Use this only when the target consumer cannot safely follow symlinks back into
the repository. `systemd-logind` is one such consumer: its service runs with
`ProtectHome=yes`, so logind drop-ins under `/etc/systemd/logind.conf.d/`
cannot be Stow symlinks pointing into `$HOME`.

