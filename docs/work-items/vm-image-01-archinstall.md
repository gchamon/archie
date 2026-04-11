# Archinstall

## Status

<!--
Use a short prose status for the current state of the work item.
Supported values are `backlog`, `planned`, `doing`, `done`, `cancelled`, and `abandoned`.
`killed` is reserved for GitLab graveyard history when a managed work item is removed from the repository.
-->

Done

## Outcome

Archie should have the canonical Python automation entrypoint that controls the
`archinstall` SDK for unattended installation in the historical VM-image
pipeline.

## Decision Changes

- The historical VM-image pipeline should begin with a Python installer
  controller around the `archinstall` SDK.
- The installer should define explicit inputs for the target disk, hostname,
  user, selected bundles, and encryption behavior.
- Post-install deployment of Archie configuration should remain part of the
  installer flow so later VM-image stages can build on a consistent baseline.

## Dependencies

- None. This is the first work item in the historical VM-image sequence.

## Main Quests

- Create a Python installer controller for a VM-first Archie profile.
- Define installer inputs for the target disk, hostname, user, bundles, and
  encryption flag.
- Implement package selection flow for official repositories plus selected AUR
  packages.
- Implement post-install deployment of Archie config, including Hyprland,
  Waybar, Zsh, and the cronjobs baseline.
- Produce installer logs and machine-readable run metadata.
- Document the configuration schema, defaults, and manual-to-automated step
  mapping for the installer flow.

## Acceptance Criteria

- Unattended install can complete using the defined schema on a target virtual
  disk.
- First boot reaches a usable Archie desktop-session baseline.
- Logs and metadata are generated for each run.
- The installer flow is deterministic enough to be consumed by the cloud-init
  work item.

## Metadata

### id

vm-image-01
