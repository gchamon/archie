# ADR 0002: Use GitLab As Canonical Upstream With GitHub Mirror

<!--toc:start-->

- [ADR 0002: Use GitLab As Canonical Upstream With GitHub Mirror](#adr-0002-use-gitlab-as-canonical-upstream-with-github-mirror)
  - [Context](#context)
  - [Decision](#decision)
  - [Alternatives Considered](#alternatives-considered)
    - [1. Keep GitHub as the canonical upstream](#1-keep-github-as-the-canonical-upstream)
    - [2. Use both GitHub and GitLab as writable upstreams](#2-use-both-github-and-gitlab-as-writable-upstreams)
    - [3. Mirror all branches to GitHub](#3-mirror-all-branches-to-github)
  - [Rationale](#rationale)
  - [Consequences](#consequences)
<!--toc:end-->

- Status: Accepted
- Date: 2026-03-21

## Context

Archie currently uses GitHub as its only configured git remote and the current
working branch is prepared for a GitHub pull request. That setup no longer
matches the intended collaboration model.

The desired future state is:

- GitLab is the canonical upstream repository.
- code review happens in GitLab merge requests
- GitHub remains available as a read-only public mirror
- the mirror stays current for the default branch and release tags

This decision needs to be explicit because repository hosting affects clone
URLs, review workflow, maintainer runbooks, and contributor expectations.

## Decision

Adopt `gitlab.com` as Archie’s canonical upstream and maintain GitHub as a
read-only mirror.

Under this decision:

- GitLab is the authoritative location for branches, merge requests, and tags.
- GitHub mirrors `main` and tags only.
- GitHub is not a supported contribution surface for pull requests or issues.
- migration should happen before opening review for the current
  `docs/planning-framework` branch, so that branch is reviewed in GitLab.

## Alternatives Considered

### 1. Keep GitHub as the canonical upstream

Rejected because it does not match the intended long-term hosting model.

### 2. Use both GitHub and GitLab as writable upstreams

Rejected because dual-write collaboration creates avoidable process ambiguity,
review split, and synchronization risk.

### 3. Mirror all branches to GitHub

Rejected because the stated goal only requires a public mirror of the default
branch and tags. Mirroring feature branches increases noise and maintenance
cost without improving the canonical workflow.

## Rationale

GitLab-first collaboration gives Archie a single authoritative place for code
review and repository administration while preserving GitHub as a public-facing
distribution channel.

Mirroring only `main` and tags keeps the public copy current without implying
that GitHub remains an equal collaboration surface. It also keeps the mirror
policy easy to understand and verify.

## Consequences

- maintainer and contributor documentation must point to GitLab as canonical
- local remote naming and setup guidance must be updated
- a mirror mechanism from GitLab to GitHub must be configured and documented
- GitHub repository settings should redirect contributions to GitLab
- temporary cutover steps should be tracked separately from this ADR in an
  execution-oriented migration document
