# ADR 0001: Use GNU Stow For Config Deployment

- Status: Accepted
- Date: 2026-03-21

## Context

Archie currently documents and relies on a deployment model built from two
different mechanisms:

- `rsync` copies the repository into target locations such as `~/.config` and
  selected system paths.
- manual symlinks are created separately for files such as `.zshrc` and
  Powerlevel10k profiles.

This model has several problems:

- the repository layout assumes direct placement under `~/.config`
- deployed state can drift from repository state after copied files are edited
- migration and cleanup behavior are hard to describe consistently
- deployment spans multiple target roots, including home files, XDG config,
  shell library paths, and selected system-managed files

The repo’s work item and session history also established an additional
requirement: Archie should be deployable while cloned outside the target
directories, without changing the runtime paths expected by Hyprland, zsh, and
other tools.

## Decision

Adopt GNU Stow as the primary deployment mechanism for Archie-managed
configuration files.

Under this decision:

- Stow manages symlinked deployment for the tracked files that belong in the
  user home, XDG config tree, shell library paths, and selected system-level
  targets.
- machine-specific generated files derived from `.dist` templates remain
  outside Stow management when they must be edited per device
- privileged deployment steps may use helper commands or wrapper scripts, but
  Stow remains the underlying model

## Alternatives Considered

### 1. Keep `rsync` as the primary deployment mechanism

Rejected because copying files into target directories makes drift likely,
assumes repo placement in deployed paths, and does not provide a clean model
for inspecting or undoing deployment changes.

### 2. Keep the mixed `rsync` plus manual symlink model

Rejected because it preserves the current inconsistency. Different parts of the
system would still be deployed by different rules, making onboarding,
maintenance, and recovery harder to document.

### 3. Build a custom symlink-management wrapper without Stow

Rejected because it would recreate behavior that Stow already provides while
adding bespoke maintenance burden. Archie benefits more from adopting a
well-known symlink-management tool than from owning a custom implementation.

### 4. Defer standardization and continue the current manual model

Rejected because the repository is already large enough that undocumented,
ad hoc deployment behavior is becoming a source of architectural ambiguity and
documentation drift.

## Rationale

GNU Stow was chosen because it provides a declarative symlink-management model
that fits Archie’s deployment needs better than copied files and manual links.

It allows:

- keeping the repository outside the final target directories
- preserving the runtime paths expected by existing configs and scripts
- making deployment and removal behavior explicit
- documenting migration from the old `rsync`-based model with clear conflict
  handling rules
- reducing divergence between what is tracked in git and what is actually
  deployed on the machine

This rationale was reconstructed from existing repo documentation and Codex
session history that analyzed the old `rsync` flow and proposed the Stow-based
replacement as the new deployment model.

## Consequences

- the repository layout must become Stow-friendly
- documentation must stop treating `rsync` as the primary deployment path
- migration guidance is required for systems that were previously deployed by
  copying files
- system-level targets may need explicit privileged commands or helper wrappers
- future deployment-related work item planning should be framed around deployment
  management, not around Stow as an epic name
