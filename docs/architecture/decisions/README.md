# Architecture Decisions

This directory contains Archie architecture decision records (ADRs).

ADR filenames follow the pattern `NNNN-short-decision-title.md`, where `NNNN`
is a zero-padded sequence number.

Current decisions:

- `0001-use-gnu-stow-for-config-deployment.md`: records why Archie chose GNU
  Stow as the deployment mechanism for managed configuration files.
- `0002-use-gitlab-as-canonical-upstream-with-github-mirror.md`: records why
  Archie uses GitLab as the canonical upstream while keeping GitHub as a
  read-only mirror of `main` and tags.
