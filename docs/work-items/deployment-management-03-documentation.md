# Milestone 3: Rewrite The Deployment Documentation

Update the written guides after the Stow layout has been implemented and
validated.

## Outcome

The docs describe the real Stow-based deployment flow, including migration from
the old `rsync` method.

## Decision changes

- The shell library package is `local` targeting `$HOME/.local`, with tracked
  files deployed under `~/.local/lib/zsh/`.
- `~/.local/lib/zsh/overrides.sh` is a machine-specific generated file that
  remains outside Stow and Git management. The tracked template is
  `overrides.dist.sh`, and local setups should ignore the generated
  `overrides.sh`.
- Documentation for machine-specific generated files must treat deployed `.dist`
  files as symlinked templates, not copied files. User-facing instructions
  should resolve the deployed template path with `readlink` before creating the
  local file beside it.
- The migration-rehearsal guidance should stay package-driven: conflict backup
  steps are generated from the Stow package contents rather than from hardcoded
  file lists.

## Tasks

- Add `stow` to the required package lists where appropriate.
- Replace the main Archie deployment instructions that currently use `rsync`
  and manual symlinks.
- Update zsh deployment guidance so `.zshrc`, `.p10k*`, and
  `~/.local/lib/zsh` are described as Stow-managed where applicable.
- Document the machine-specific zsh override flow for
  `~/.local/lib/zsh/overrides.sh`, including the tracked
  `overrides.dist.sh` template and the fact that `overrides.sh` remains
  untracked.
- Update system-level deployment docs for cronjobs and keyboard
  customizations if they are part of the Stow model.
- Add a migration guide that answers whether Stow can be applied on top of a
  prior `rsync` deployment and explains the required conflict cleanup.
- Replace any remaining `.dist` setup instructions that assume copied files
  with symlink-aware guidance. Generated files such as
  `hypr/config/device.conf`, `hyprpaper.conf`, and `~/.local/lib/zsh/overrides.sh`
  should be created from the deployed `.dist` symlink targets by resolving
  them with `readlink`, then writing the local machine-specific file beside
  the real template path.
- Update internal repo guidance such as `CLAUDE.md` so agent-facing deployment
  instructions match the new model.

## Exit Criteria

- No primary deployment doc tells users to deploy Archie with `rsync`.
- The migration path from the old deployment model is documented clearly.
- The docs explain how machine-specific files derived from deployed `.dist`
  templates are created in a Stow deployment without treating the templates as
  copied files.
- Internal and user-facing docs agree on the deployment model.
