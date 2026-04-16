# Infrastructure

## Status

Doing

## Outcome

Archie's repository tooling should enforce consistency between code and its
documentation automatically. Maintenance burden caused by documentation drift
should be detected early and corrected with guided suggestions rather than
discovered by readers encountering stale content.

## Work items

- [infrastructure-01-automated-documentation-maintenance](/docs/work-items/infrastructure-01-automated-documentation-maintenance.md)

## Decision Changes

_None yet._

## Main Quests

- Design and implement automated tooling that detects drift between shell
  library source files and their co-located READMEs.

## Acceptance Criteria

- The epic exposes a stable `id` and explicit `child_ids`.
- At least one tool exists under the `archie` CLI that enforces documentation
  consistency without requiring manual audits.

## Metadata

### id

infrastructure

### child_ids

- infrastructure-01

### priority

normal
