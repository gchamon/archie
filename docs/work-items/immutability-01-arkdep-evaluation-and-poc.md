# Evaluate Arkdep For Archie And Run A Vacuum POC

Determine whether Archie should adopt `arkdep` as the basis for an immutable
system-dependency track by validating it in a tightly controlled disposable VM
before any host-side integration work begins.

## Status

Backlog

## Outcome

Archie has a concrete go, no-go, or defer recommendation for `arkdep`, backed
by repo-documented evaluation criteria and a proof of concept executed in a new
disposable VM created from the existing reproducible image path.

## Decision Changes

- The first immutability milestone is evaluation plus proof of concept, not
  direct migration of the current Archie host.
- The proof of concept must run in a fresh disposable VM so failure and
  rollback behavior can be observed without risking the workstation.
- The VM should be created from the current reproducible image workflow so the
  POC starts from a known and controllable state.
- Archie should validate `arkdep` against its existing Stow-managed deployment
  model and quickstart assumptions instead of assuming those layers will be
  rewritten.
- If `arkdep` is not a fit, the next planning step should pivot to a delayed
  updater that inventories installed packages and resolves historical versions
  through the Arch Linux Archive.

## Main Quests

- Define the evaluation criteria that matter for Archie, including:
  - installation and bootstrap prerequisites
  - filesystem and boot assumptions
  - update and rollback behavior
  - package layering model
  - operational complexity for a single-user Arch workstation
- Compare those criteria against Archie's current architecture, especially:
  - Stow-managed deployment roots
  - quickstart automation
  - current `pacman` and `yay` helper expectations
  - the dev-env and reproducible image workflow
- Stand up a new disposable VM from the existing tested image path dedicated to
  the `arkdep` proof of concept.
- Execute a narrow POC in that VM that:
  - installs and initializes `arkdep`
  - exercises at least one deployment or update cycle
  - validates how rollback or generation switching is expected to work
  - probes whether Archie-managed configuration and package expectations can be
    mapped cleanly onto the model
- Capture concrete points of friction, unsupported assumptions, and operator
  burdens discovered during the POC.
- Produce a recommendation with one of these explicit outcomes:
  - proceed with an `arkdep` adoption track
  - reject `arkdep` and plan the Arch Linux Archive delayed-updater track
  - defer because blocking platform prerequisites make the decision premature
- Define the next work items required for the chosen outcome.

## Acceptance Criteria

- The work item records Archie-specific evaluation criteria instead of generic
  immutable-distro talking points.
- A new disposable VM is used for the proof of concept.
- The proof of concept reaches a point where `arkdep` installation and at least
  one deployment-related workflow can be evaluated concretely.
- The recommendation is tied to observed results and names the next work item
  sequence for the selected branch.
- If `arkdep` is rejected or deferred, the work item names the delayed-update
  manager as the fallback path rather than leaving the alternative undefined.

## Metadata

### id

immutability-01

## Implementation Notes

- Canonical evaluation target: `arkdep`
- Isolation boundary: a new disposable VM launched from the existing Archie
  reproducible image path
- Architecture references to review during execution:
  `docs/epics/dev-env.md`, `docs/development/DEV_ENV.md`, and
  `scripts/launch-archie-instance.sh`
- Fallback direction if rejected: Archie-managed delayed updates built around
  Arch Linux Archive package/version resolution rather than mirrorlist mutation
