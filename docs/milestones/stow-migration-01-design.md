# Milestone 1: Design The Stow Deployment Model

Define the target deployment model before changing the repo structure or the
docs.

## Outcome

A decision-complete Stow layout for Archie, including package boundaries,
deployment targets, and migration behavior from the old `rsync`-based setup.

## Tasks

- Decide the Stow package layout for:
  - home-level files under `~`
  - XDG config files under `~/.config`
  - shell library files under `~/.local/lib/zsh`
  - system-level files under `/etc`
  - XKB files under `/usr/share/xkeyboard-config-2`
- Decide whether system-level deployment should use `sudo stow` directly or a
  wrapper script that invokes it.
- Identify repo files that currently assume the repo itself lives at
  `~/.config` and verify they will still resolve correctly after deployment.
- Define migration rules for machines previously deployed with `rsync`,
  especially conflict handling for copied files versus existing symlinks.
- Define what remains outside Stow management, such as machine-specific files
  derived from `.dist` templates.

## Exit Criteria

- The target Stow commands are known.
- The target directory layout is known.
- The migration behavior is clear enough to document without caveats.
