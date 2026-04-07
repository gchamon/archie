# Deployment Management

## Status

Done

## Outcome

Archie should use a durable deployment-management model that separates tracked
configuration into clear Stow-owned package roots, preserves runtime paths
after deployment, and documents both clean install and migration behavior.

## Decision Changes

- GNU Stow is the accepted deployment mechanism for Archie’s tracked home, XDG,
  local-library, and system-managed paths.
- The deployment-management effort is broader than any single command; it also
  includes repository structure, migration behavior, and operator
  documentation.
- The completed implementation sequence should remain documented because later
  automation work depends on the same deployment boundaries.

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

### priority

critical
