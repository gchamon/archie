# Automate Archie Deployment Inside The Dev Env VM

Turn the validated manual Archie installation and deployment flow into a
repo-owned automation path that runs inside the dev-env VM environment.

## Status

<!--
Use a short prose status for the current state of the work item.
Supported values are `backlog`, `planned`, `doing`, `done`, `cancelled`, and `abandoned`.
`killed` is reserved for GitLab graveyard history when a managed work item is removed from the repository.
-->

Planned

## Outcome

After the manual VM workflow is proven useful, Archie can be applied inside the
reproducible guest through a documented automation entrypoint that follows the
real Stow-based deployment model used by the project.

## Decision Changes

- This work item starts only after the manual Archie workflow in work item 1 is
  validated enough to serve as the source of truth for automation.
- Archie deployment automation should follow the documented Arch plus Stow
  deployment model rather than reintroducing `archinstall` as the deployment
  interface.
- The dev-env VM contract from work item 1 remains authoritative. This work
  builds on it instead of redefining provisioning or runtime management.
- Automation should cover the guest-side Archie deployment flow, but avoid
  overreaching into image pipeline or release artifact concerns.
- Work item 1 now defines the reproducible artifact as a locally published Incus
  image alias created from a stopped bootstrap VM.
- Work item 1 also establishes a second launch-time cloud-init payload for
  per-instance guest setup, currently used to write `~/pull-archie-repo.sh` for
  the Archie user.

## Main Quests

- Capture the validated manual Archie deployment flow from work item 1 and turn
  it into an explicit automation contract.
- Define the automation entrypoint and its required inputs, including:
  - repo path or checkout strategy inside the guest
  - target user assumptions
  - package profile or required package set
  - any safe defaults needed for VM-specific local files
- Implement or specify the guest-side steps needed to:
  - install required Archie dependencies
  - acquire the Archie repository in the guest
  - run the Stow deployment for home, config, local, and system-managed paths
  - scaffold any required local files from deployed `.dist` templates when
    necessary for the VM
- Define which Archie capabilities must be working in the automated baseline,
  such as:
  - Hyprland session startup
  - Waybar
  - Dunst
  - shell setup
  - networking retained after deployment
- Define the expected automation outputs, logs, and failure modes so deploy
  issues are actionable.
- Document the manual follow-up expectations that remain intentionally out of
  scope if the automation should not guess machine-specific values.

## Acceptance Criteria

- Archie can be deployed inside the dev-env VM through a repo-owned documented
  automation path.
- The deployed guest reaches a basic Archie desktop baseline suitable for
  install-script and feature testing.
- Deployment failures produce actionable logs that distinguish bootstrap,
  deployment, and session startup failures.
- The automation reuses the dev-env assumptions from work item 1 without
  introducing a separate runtime model.

## Metadata

### id

dev-env-02
