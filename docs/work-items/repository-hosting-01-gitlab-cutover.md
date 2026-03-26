# GitLab Canonical Upstream Cutover

Move Archie from GitHub-only hosting to a GitLab-first workflow while keeping
GitHub as a read-only mirror of `main` and tags.

## Status

Complete.

## Goal

Finish the hosting cutover before opening review for `docs/planning-framework`,
so that the branch is reviewed as a GitLab merge request.

## Expected Outcome

- GitLab is the canonical upstream with `main` as the default branch.
- GitHub mirrors `main` and tags from GitLab.
- documentation clearly states that GitLab is canonical and GitHub is
  read-only
- the current `docs/planning-framework` branch is pushed to GitLab and opened
  there for review

## Execution Checklist

1. Create the new `gitlab.com` repository and confirm `main` will be the
   default branch.
2. Push the full repository history to GitLab and verify `main` and tags are
   present.
3. Configure GitLab as the canonical writable remote for local clones.
4. Configure one-way mirroring from GitLab to GitHub for `main` and tags.
5. Lock down GitHub collaboration surfaces so they redirect contributors to
   GitLab.
6. Update repository docs and repository descriptions to describe the new
   canonical host and mirror policy.
7. Verify that a change merged to GitLab `main` appears in GitHub `main`.
8. Verify that a new annotated tag pushed to GitLab appears in GitHub.
9. Push `docs/planning-framework` to GitLab and open the merge request there.

## Key Tasks

- create or rename remotes so `origin` points to GitLab and GitHub is kept as
  a separate mirror remote
- document the contribution policy in the README, development docs, and ADRs
- record the mirror owner, credential type, and failure-recovery steps in the
  maintainer workflow
- check for any hardcoded GitHub clone URLs before declaring the migration
  complete

## Dependencies

- a GitLab namespace and repository must exist
- a GitHub credential or deploy token for mirror pushes must be available if
  GitLab-managed push mirroring requires one
- repository settings access is required on both hosting providers
