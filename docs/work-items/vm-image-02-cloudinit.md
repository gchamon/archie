# Work Item: Cloudinit

<!--toc:start-->

- [Work Item: Cloudinit](#work-item-cloudinit)
  - [Goal](#goal)
  - [Scope](#scope)
  - [Out of Scope](#out-of-scope)
  - [Inputs](#inputs)
  - [Deliverables](#deliverables)
  - [Acceptance Criteria](#acceptance-criteria)
  - [Dependencies](#dependencies)
<!--toc:end-->

## Goal
Create the cloud-init wrapper that provisions a base Arch cloud image and executes the Archie `archinstall` automation non-interactively.

## Scope
- Use official Arch Linux cloud images from `arch-boxes` as base artifacts.
- Create `cloud-init` user-data and meta-data templates for unattended provisioning.
- Install and invoke the Python archinstall controller within the provisioning flow.
- Capture serial console and cloud-init logs for troubleshooting.
- Define parameterization strategy for installer config injection.

## Out of Scope
- Long-term image publishing workflow.
- End-to-end CI policy enforcement (covered in later work items).
- Calamares integration.

## Inputs
- Official Arch cloud images (QCOW2).
- QEMU cloud-init drive/seed mechanism.
- Output contract from the `ARCHINSTALL` work item.

## Deliverables
- Cloud-init templates (`user-data`, `meta-data`) for Archie provisioning.
- Wrapper script to assemble seed image and pass runtime parameters.
- Documentation for local execution and debug workflow.
- Failure handling expectations (timeouts, retries, log collection).

## Acceptance Criteria
- Provisioning boots from official Arch cloud image and runs unattended.
- Cloud-init successfully triggers archinstall automation end-to-end.
- Resulting VM disk reaches installed Archie state and can boot.
- Logs clearly identify where failures occur (cloud-init vs installer logic).

## Dependencies
- `docs/work-items/vm-image-01-archinstall.md` completed outputs.
