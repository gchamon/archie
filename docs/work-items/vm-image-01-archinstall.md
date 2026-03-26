# Work Item: Archinstall

## Goal
Build the canonical Python automation entrypoint that controls the `archinstall` SDK for unattended Archie installation.

## Scope
- Create a Python installer controller for a VM-first Archie profile.
- Define installer inputs (target disk, hostname, user, bundles, encryption flag).
- Implement package selection flow for official repos plus selected AUR.
- Implement post-install deployment of Archie config (Hyprland, Waybar, Zsh, cronjobs baseline).
- Produce installer logs and machine-readable run metadata.

## Out of Scope
- Custom ISO generation.
- Calamares integration.
- Hardware-specific tuning for Nitro 5 (deferred until after VM baseline stability).

## Inputs
- Archie repository as source of truth for desktop config.
- Archinstall Python SDK.
- Package manifests curated for this phase.

## Deliverables
- Python installer module and executable entry script.
- Installer configuration schema file (documented keys and defaults).
- Post-install orchestration script(s) invoked by installer flow.
- Work item documentation mapping manual guide steps to automated steps.

## Acceptance Criteria
- Unattended install can complete using the defined schema on a target virtual disk.
- First boot reaches a usable Archie desktop session baseline.
- Logs and metadata are generated for each run.
- Installer flow is deterministic enough to be consumed by the cloud-init work item.

## Dependencies
- None (first work item in this phase).
