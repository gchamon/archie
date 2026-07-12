# Investigate Fedora Silverblue Feasibility For Archie

Run a bounded spike to determine whether Archie can reasonably target Fedora
Silverblue as an immutable workstation host, and whether doing so would extend
the current Archie architecture or require a separate Fedora-specific product
line.

## Status

Backlog

## Outcome

Archie has a concrete feasibility recommendation for Fedora Silverblue, backed
by a written compatibility matrix, a narrow disposable-VM proof of concept, and
an explicit decision about whether a Silverblue track belongs inside the
immutability epic.

## Decision Changes

- Fedora Silverblue is treated as an exploratory host target, not as a
  replacement for the current Arch-based Archie workflow.
- The spike must evaluate the cost of supporting a non-Arch host before any
  production changes are made to package installation, deployment, or user
  documentation.
- The recommendation must distinguish between "Archie can run on Silverblue"
  and "Archie can be maintained well on Silverblue".
- Silverblue-specific package layering, `rpm-ostree`, Flatpak, Toolbox or
  Distrobox, SELinux, and systemd user-service behavior must be evaluated
  against Archie's current Stow-managed model.
- If the spike recommends proceeding, follow-up work items must define the
  supported host boundary and avoid quietly making the Arch path harder to
  maintain.

## Scope Notes

Included:

- Research the current Fedora Silverblue operating model and document the parts
  that matter to Archie.
- Compare Archie assumptions against Silverblue constraints, including package
  management, mutable paths, system configuration, user configuration,
  developer tooling, display-manager/session integration, and rollback.
- Run a narrow disposable-VM proof of concept that deploys a representative
  subset of Archie onto Fedora Silverblue.
- Produce a feasibility recommendation and downstream work-item shape.

Not included:

- Rewriting Archie installation scripts for Fedora.
- Supporting Fedora Workstation, Kinoite, Universal Blue, or other atomic
  variants unless they are mentioned only as comparison points.
- Replacing the existing Arch Linux target or changing the default bootstrap
  path.
- Committing long-lived Silverblue deployment assets before the spike reaches a
  proceed recommendation.

## Main Quests

### 1. Define the compatibility matrix

Document the Archie assumptions that must be tested against Silverblue:

- package installation currently expected through `pacman` and `yay`
- Stow-managed files under `$HOME`, `$HOME/.config`, `$HOME/.local`, `/etc`,
  and `/usr/share/xkeyboard-config-2`
- Hyprland session startup, display-manager integration, Wayland utilities, and
  desktop portals
- shell and development tooling assumptions in `.zshrc`,
  `deployment-packages/local/`, and the dev-env workflow
- package sets that could map to layered RPMs, Flatpaks, containers, or
  generated artifacts
- SELinux, immutable root, and `/usr` constraints that affect scripts or
  deployment packages
- rollback behavior and how it compares with the `arkdep` and delayed-update
  tracks

For each row, classify the fit as native, adaptable, blocked, or unknown, with
a one-line rationale and a candidate mitigation where relevant.

### 2. Disposable-VM proof of concept

Create a disposable Fedora Silverblue VM for the spike. Keep all throwaway
assets outside the production deployment path unless the recommendation later
green-lights follow-up work.

Exercise a representative subset of Archie:

- install or layer the minimum system packages required to start a Hyprland
  session
- deploy the `home`, `config`, and `local` Stow packages into a test user
  account
- evaluate what happens to `/etc` and XKB deployment packages under
  Silverblue's filesystem model
- validate whether zsh startup, Kitty, Waybar, Rofi, Dunst, clipboard tooling,
  and desktop portals can run without Arch-specific assumptions
- test one update and rollback path using Silverblue's native mechanisms
- record friction, blocked assumptions, and any host-specific patches needed

### 3. Package and runtime strategy

Map the current package universe into Silverblue deployment categories:

- layered RPM
- Flatpak
- Toolbox or Distrobox
- user-local binary or generated artifact
- unsupported or requires custom packaging

Pay special attention to Hyprland, Waybar, Rofi Wayland, SDDM integration,
fonts, zsh plugins, development tools, and AUR-only packages. Record whether
each category can be maintained with acceptable operator effort.

### 4. Recommendation and follow-up shape

Produce one of these recommendations:

- proceed with a Silverblue adoption track
- keep Silverblue as a documented experimental host only
- reject Silverblue as an Archie target
- defer because upstream or Archie prerequisites are not mature enough

If proceeding or deferring, name the next work items required. At minimum,
define whether future work should create Fedora-specific install automation,
host capability detection, package-manifest partitioning, deployment docs, or a
dedicated VM test path.

## Acceptance Criteria

- The compatibility matrix covers package management, Stow deployment roots,
  Hyprland/session integration, `/etc`, XKB, development tooling, SELinux,
  immutable-root behavior, and rollback.
- A disposable Fedora Silverblue VM is used for the proof of concept.
- The proof of concept deploys a representative subset of Archie and records
  concrete friction notes instead of relying only on desk research.
- The package and runtime strategy classifies the important current Archie
  package groups into Silverblue-compatible deployment categories.
- The recommendation explicitly states whether Silverblue should become a
  supported Archie target, an experimental target, a rejected target, or a
  deferred target.
- Any proceed or defer recommendation names the next work items and the
  production files they would be allowed to touch.

## Metadata

### id

immutability-02

## Implementation Notes

- Treat this as a spike. Production changes should wait for the recommendation.
- Fedora Silverblue references should be checked against current upstream
  documentation during execution because the atomic-desktop packaging model and
  recommended tooling can change.
- Compare the result with `immutability-01` so the epic can decide whether
  Silverblue complements, competes with, or replaces the `arkdep` investigation.
