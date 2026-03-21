# Milestone 2: Restructure The Repo For Deployment Management

Reorganize the repository so the deployment model from Milestone 1 is real and
executable.

## Outcome

The repo can be cloned outside the target directories and deployed with Stow
into the intended home and system roots.

## Tasks

- Move tracked files into a Stow-friendly package layout.
- Preserve the deployed target paths used by Hyprland, zsh, and other tools.
- Add any helper commands or scripts needed to apply or remove Stow-managed
  packages consistently.
- Verify that the deployed paths still match the hardcoded runtime paths in the
  configs and scripts.
- Validate a clean deployment flow on a machine with no previous Archie install.
- Validate migration behavior on a machine that previously used the `rsync`
  deployment flow.

## Exit Criteria

- `stow` can deploy the intended packages into the correct targets.
- Existing Archie functionality still resolves files from the expected paths.
- Migration from the old deployment method has been exercised and any required
  cleanup steps are known.
