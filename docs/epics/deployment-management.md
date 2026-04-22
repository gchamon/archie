# Deployment Management

## Status

Doing

## Outcome

Archie should use a durable deployment-management model that separates tracked
configuration into clear Stow-owned package roots, preserves runtime paths
after deployment, and documents both clean install and migration behavior.


## Work items

- [deployment-management-01-design](/docs/work-items/deployment-management-01-design.md)
- [deployment-management-02-restructure](/docs/work-items/deployment-management-02-restructure.md)
- [deployment-management-03-documentation](/docs/work-items/deployment-management-03-documentation.md)
- [deployment-management-04-quickstart-automation](/docs/work-items/deployment-management-04-quickstart-automation.md)
- [deployment-management-05-uninstall-automation](/docs/work-items/deployment-management-05-uninstall-automation.md)
- [deployment-management-06-flat-packages-manifest](/docs/work-items/deployment-management-06-flat-packages-manifest.md)

## Decision Changes

- GNU Stow is the accepted deployment mechanism for Archie’s tracked home, XDG,
  local-library, and system-managed paths.
- The deployment-management effort is broader than any single command; it also
  includes repository structure, migration behavior, and operator
  documentation.
- The completed implementation sequence should remain documented because later
  automation work depends on the same deployment boundaries.
- Re-opened to plan a manifest-driven flat-package layout that decouples
  package directory names from their stow target roots.

## Main Quests

- Define the deployment model and package boundaries.
- Restructure the repository so the deployment model is directly executable.
- Document the resulting deployment, quickstart, and uninstall flows.

## Acceptance Criteria

- The epic explains the deployment-management outcome without requiring readers
  to infer it from implementation history alone.
- The epic exposes a stable `id` and explicit `child_ids`.
- The epic reflects that this track is complete and available as durable
  planning history.

## Metadata

### id

deployment-management

### child_ids

- deployment-management-01
- deployment-management-02
- deployment-management-03
- deployment-management-04
- deployment-management-05
- deployment-management-06

### priority

critical
