# GitLab Canonical Upstream Cutover

Move Archie from GitHub-only hosting to a GitLab-first workflow while keeping
GitHub as a read-only mirror of `main` and tags.

## Status

<!--
Use a short prose status for the current state of the work item.
Supported values are `backlog`, `planned`, `doing`, `done`, `cancelled`, and `abandoned`.
`killed` is reserved for GitLab graveyard history when a managed work item is removed from the repository.
-->

Done

## Outcome

GitLab is the canonical upstream for Archie with `main` as the default branch,
GitHub mirrors `main` and tags from GitLab as a read-only replica, and the
repository documentation and maintainer workflow describe that hosting model
clearly.

## Decision Changes

- GitLab should be the writable canonical upstream for Archie.
- GitHub should remain available as a read-only mirror of `main` and tags.
- The hosting cutover should land before review on `docs/planning-framework`
  so that the branch is reviewed as a GitLab merge request.

## Dependencies

- A GitLab namespace and repository must exist.
- A GitHub credential or deploy token for mirror pushes must be available if
  GitLab-managed push mirroring requires one.
- Repository settings access is required on both hosting providers.

## Main Quests

- Create the GitLab repository and confirm `main` is the default branch.
- Push the full repository history to GitLab and verify `main` and tags are
  present.
- Configure GitLab as the canonical writable remote for local clones.
- Configure one-way mirroring from GitLab to GitHub for `main` and tags.
- Lock down GitHub collaboration surfaces so they redirect contributors to
  GitLab.
- Update repository docs and repository descriptions to describe the canonical
  host and mirror policy.
- Verify that a change merged to GitLab `main` appears in GitHub `main`.
- Verify that a new annotated tag pushed to GitLab appears in GitHub.
- Push `docs/planning-framework` to GitLab and open the merge request there.
- Record the mirror owner, credential type, and failure-recovery steps in the
  maintainer workflow.
- Check for hardcoded GitHub clone URLs before declaring the migration
  complete.

## Acceptance Criteria

- GitLab is the canonical upstream with `main` as the default branch.
- GitHub mirrors `main` and tags from GitLab as a read-only replica.
- Repository documentation states that GitLab is canonical and GitHub is
  read-only.
- The `docs/planning-framework` branch is pushed to GitLab and opened there
  for review.

## Metadata

### id

repository-hosting-01
