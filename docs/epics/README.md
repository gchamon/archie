# Epics

<!--toc:start-->

- [Epics](#epics)
  - [Metadata](#metadata)
  - [Current Epics](#current-epics)
    - [`deployment-management`](#deployment-management)
    - [`vm-image`](#vm-image)
    - [`dev-env`](#dev-env)
<!--toc:end-->

This directory defines the high-level initiatives represented by work item files
in `docs/work-items`.

Each epic groups a sequence of work item documents that belong to the same
larger change effort.

For more information, see <https://docs.gitlab.com/user/group/epics/>.

Epics in this directory default to priority `normal` unless overridden in
metadata.

Project critical-chain rule:

- work items linked to epics with priority `critical` form the critical chain
  of the project
- epics with priority `high` are important but do not automatically place
  their work items on the critical chain

## Metadata

Epics may include a `## Metadata` subsection near the top when they need to
override default epic attributes.

- `priority` defaults to `normal` when omitted.
- Supported explicit `priority` values are `critical`, `high`, and `normal`.
- `## Metadata` should treat metadata as nested Markdown structure.
- Each metadata key should be a `###` heading under `## Metadata`.
- The value should appear as the body content directly under that `###` key
  heading.

Example:

```md
## Metadata

### priority

critical
```

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

This epic is now historical planning context. The active direction for new VM
work is `dev-env`.

### `dev-env`

This epic covers building a repeatable Archie development VM workflow around an
Incus-managed Arch guest. It starts with cloud-init bootstrap to a
graphical-ready baseline, then layers Archie deployment automation and only
later standardizes runtime operations and smoke tests where they prove useful.

This initiative was previously named `reproducible-environment`. The shorter
`dev-env` name is now the canonical term across docs, scripts, and planning
artifacts.
