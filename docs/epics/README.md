# Epics

This directory defines the high-level initiatives represented by milestone files
in `docs/milestones`.

Each epic groups a sequence of milestone documents that belong to the same
larger change effort.

## Current Epics

### `deployment-management`

This epic covers how Archie configuration is deployed and maintained across
home, XDG, and system-managed paths. It includes standardizing the deployment
model, restructuring the repository to support that model, and rewriting the
documentation so deployment and migration are consistent.

GNU Stow is the current architectural choice used to implement this epic, but
the epic itself is about deployment management rather than any single tool.

### `vm-image`

This epic covers building Archie as an unattended VM image pipeline. It starts
with `archinstall` automation, then layers cloud-init provisioning, QEMU image
creation, and automated validation so Archie can be built and tested as a
repeatable virtual machine artifact.
