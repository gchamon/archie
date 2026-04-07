# Add Uninstall Automation For Archie Deployment

Carry the deferred uninstall helper work into its own tracked stage now that
the install flow has landed separately as `scripts/install.sh`.

## Status

Planned

## Outcome

Archie has a dedicated, tracked plan for uninstall automation that can be
implemented independently from the install flow while staying aligned with the
canonical migration and rollback guides.

## Decision Changes

- The uninstall helper is no longer tracked as part of the completed
  quickstart/install work item. It is now its own follow-up stage under the
  `deployment-management` epic.
- The intended uninstall entrypoint remains `scripts/uninstall.sh`.
- The uninstall flow should stay derived from the documented Stow deployment
  and rollback model, not invent a new removal model.
- The first implementation phase should focus on Archie-managed symlink cleanup
  and restoration of moved-aside backup paths.
- Package removal remains a later phase of the uninstall work and should be
  designed only after the restore-focused phase is stable.
- `docs/user/MIGRATING.md` remains the canonical source for rollback semantics
  until uninstall automation is implemented and documented against it.
- The uninstall helper should operate against the current `scripts/install.sh`
  backup layout and environment contract, including:
  - `~/archie-pre-stow-backup`
  - `/root/archie-pre-stow-backup`
  - the optional feature toggles that affect deployed targets

## Dependencies

- [Work Item 1](deployment-management-01-design.md) defines the Stow deployment
  model the uninstall helper must reverse.
- [Work Item 2](deployment-management-02-restructure.md) made the package
  layout and target roots concrete.
- [Work Item 3](deployment-management-03-documentation.md) made the migration
  and rollback documentation canonical.
- [Work Item 4](deployment-management-04-quickstart-automation.md) defined the
  install helper contract and the original staged uninstall intent, but it is
  already complete and should not be revised further.

## Scope Notes

Included:

- Define the executable boundary and responsibilities for `scripts/uninstall.sh`.
- Define the restore-focused uninstall phase against the current Stow and
  backup layout.
- Define the later package-state reversal phase as explicit follow-up work.
- Define the documentation touchpoints that must stay aligned with uninstall
  behavior.

Not included:

- Reworking `scripts/install.sh` beyond the contract needed for uninstall
  compatibility.
- Broad package-management redesign outside the uninstall use case.
- Full implementation of package-state snapshots unless the restore-focused
  uninstall phase proves stable first.

## Main Quests

- Define the uninstall helper interface, including:
  - repo-local execution as `./scripts/uninstall.sh`
  - visible execution phases
  - failure behavior when expected backup state is missing
- Define phase 1 as restore-focused uninstall automation:
  - remove Archie-managed Stow links from home, config, local, and supported
    `/etc` targets
  - restore backed-up conflicting paths from the install backup roots when
    present
  - respect the same optional deployment toggles used by install for
    `/etc`-target packages
- Define how uninstall should detect whether a target path is Archie-managed,
  already absent, or locally modified outside Archie ownership.
- Define the minimum user-facing documentation needed once uninstall exists,
  including how it relates to `docs/user/MIGRATING.md`.
- Define phase 2 package-state reversal separately from phase 1:
  - capture what install-side data must exist to support safe removal of
    Archie-added explicit packages
  - compare pre-install and current package state conservatively
  - avoid removing packages that were present before Archie install or were
    added later for unrelated reasons
- Define the validation strategy for uninstall automation, including at least:
  - dry-run or observable phase output
  - restore verification against a test deployment
  - failure handling when backup roots are partial or missing

## Acceptance Criteria

- Archie has a dedicated work item for uninstall automation that is no longer
  buried inside the completed install-flow work item.
- The intended `scripts/uninstall.sh` behavior is explicit enough to implement
  without reopening decisions about restore scope, backup roots, or package
  removal boundaries.
- The work item keeps uninstall design aligned with the current install helper,
  Stow deployment model, and migration documentation.

## Metadata

### id

deployment-management-05
