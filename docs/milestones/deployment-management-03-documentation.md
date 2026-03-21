# Milestone 3: Rewrite The Deployment Documentation

Update the written guides after the Stow layout has been implemented and
validated.

## Outcome

The docs describe the real Stow-based deployment flow, including migration from
the old `rsync` method.

## Tasks

- Add `stow` to the required package lists where appropriate.
- Replace the main Archie deployment instructions that currently use `rsync`
  and manual symlinks.
- Update zsh deployment guidance so `.zshrc`, `.p10k*`, and
  `~/.local/lib/zsh` are described as Stow-managed where applicable.
- Update system-level deployment docs for cronjobs and keyboard
  customizations if they are part of the Stow model.
- Add a migration guide that answers whether Stow can be applied on top of a
  prior `rsync` deployment and explains the required conflict cleanup.
- Update internal repo guidance such as `CLAUDE.md` so agent-facing deployment
  instructions match the new model.

## Exit Criteria

- No primary deployment doc tells users to deploy Archie with `rsync`.
- The migration path from the old deployment model is documented clearly.
- Internal and user-facing docs agree on the deployment model.
