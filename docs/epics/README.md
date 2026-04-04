# Epics

<!--toc:start-->

- [Epics](#epics)
  - [Metadata](#metadata)
  - [Current Epics](#current-epics)
    - [`deployment-management`](#deployment-management)
    - [`vm-image`](#vm-image)
    - [`dev-env`](#dev-env)
    - [`system-gui`](#system-gui)
    - [`homepage`](#homepage)
    - [`assistant`](#assistant)
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

- Definition: [deployment-management.md](./deployment-management.md)
- Scope: Deployment and maintenance of Archie configuration across home, XDG,
  and system-managed paths.

### `vm-image`

- Definition: [vm-image.md](./vm-image.md)
- Scope: Historical VM image pipeline work around `archinstall`, cloud-init,
  QEMU image creation, and automated validation.

### `dev-env`

- Definition: [dev-env.md](./dev-env.md)
- Scope: Repeatable Archie development VM workflow around an Incus-managed Arch
  guest.

### `system-gui`

- Definition: [system-gui.md](./system-gui.md)
- Scope: First-party graphical interfaces for Archie system operations.

### `homepage`

- Definition: [homepage.md](./homepage.md)
- Scope: Archie’s public-facing homepage, product positioning, and supporting
  proof points.

### `assistant`

- Definition: [assistant.md](./assistant.md)
- Scope: An Archie assistant experience spanning GUI, TUI, and optional coding
  agent integration.
