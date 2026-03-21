# Archie Distro Plan: Arch-Based ISO With Calamares for General Users

## Summary
Build `Archie` as a custom Arch-based live ISO with a Calamares GUI installer, laptop-first defaults, selectable software bundles, and quarterly stable releases.  
Base stays on Arch repos + AUR (enabled broadly), with systemd-boot (UEFI) and ext4 default partitioning with optional LUKS encryption.

## Goal And Success Criteria
- Deliver a bootable x86_64 ISO that installs a working Archie desktop on supported laptops.
- Installer is GUI-first (Calamares), no manual post-install steps required for core experience.
- First boot lands in a functional Hyprland session with networking, audio, Bluetooth, Waybar, notifications, and sane defaults.
- Bundle selection works at install time (`core`, `dev`, `creator`).
- Quarterly release pipeline produces reproducible ISOs with release notes and known-issues list.

## Scope
In scope:
- Archiso profile and build pipeline.
- Calamares integration and branded installer flow.
- Migration of current guide/manual steps into automated install-time + first-boot setup.
- Laptop-first defaults and hardware guardrails.
- QA matrix and release process.

Out of scope for v1:
- Own binary package repository.
- Secure Boot enablement.
- Equal support across all desktop/server hardware classes.
- Non-UEFI boot paths as primary target.

## Architecture And Implementation Plan

### 1. Repository Layout And Ownership
- Create distro-oriented top-level structure:
  - `iso/archiso/` (archiso profile, airootfs, packages list, build scripts)
  - `iso/calamares/` (Calamares settings/modules/branding)
  - `profiles/` (bundle definitions and package manifests)
  - `scripts/release/` (build, validate, publish)
  - keep existing `hypr/`, `waybar/`, `nvim/`, etc. as source-of-truth configs
- Keep current dotfiles repo usable independently; distro layer consumes it.

### 2. Package/Bundle Model
- Define bundle manifests:
  - `core`: required desktop and session stack.
  - `dev`: current development tooling subset.
  - `creator`: media/productivity apps.
- Implement explicit package manifest files (official vs AUR separated) consumed by installer logic.
- AUR policy for v1: enabled broadly, but mark risky/large AUR packages and gate them behind bundle selection where possible.

### 3. Archiso Build
- Add archiso profile derived from upstream `releng`.
- Include live session autologin + Archie branding assets.
- Include Calamares, network tools, and installer dependencies in live environment.
- Build artifact naming format:
  - `archie-YYYY.QN-x86_64.iso` (quarterly stable naming).

### 4. Calamares Integration
- Configure modules for:
  - Locale, keyboard, timezone, user, partitioning, bootloader, packages.
- Storage default:
  - ext4 with optional LUKS path exposed in UI.
- Bootloader target:
  - systemd-boot on UEFI.
- Add bundle selection UI page mapped to manifest-driven package sets.
- Add post-install hooks for:
  - Dotfile deployment into target user.
  - Service enablement.
  - Hardware/profile templating generation.

### 5. Config Deployment Strategy
- Replace manual symlink/rsync instructions with installer/post-install automation.
- Preserve machine-specific overrides via generated `device.conf` template in installed system.
- Ensure user-owned file permissions for home configs at end of install.

### 6. Hardware Strategy (Laptop-First)
- Official v1 support target:
  - UEFI laptops, internal display + common external monitor workflows.
- Handle GPU-sensitive defaults conservatively:
  - avoid hardcoding NVIDIA-only env vars globally.
  - detect and conditionally apply GPU-specific snippets.
- Keep lid/power behavior configurable but sane by default.

### 7. Release, QA, And Operations
- Quarterly stable release cadence.
- Required pre-release checks:
  - ISO boots in UEFI VM.
  - Installer completes on clean virtual disk.
  - First boot smoke test for core desktop/session components.
  - Bundle install verification.
- Add issue triage labels:
  - `installer`, `hardware-nvidia`, `bundle-dev`, `bundle-creator`, `upgrade`.

## Public Interfaces / Types To Add
- `profiles/bundles.yaml` (or TOML):
  - bundle IDs, labels, package groups, AUR flags, conflicts.
- `profiles/packages-core.txt`, `profiles/packages-dev.txt`, `profiles/packages-creator.txt`.
- Calamares-to-manifest contract:
  - selected bundle IDs exported to install-time script.
- `release-manifest.json` per ISO:
  - build date, git commit, package manifest hashes, known issues URL.

## Test Cases And Scenarios
1. Install `core` only on UEFI VM with ext4, no encryption.
2. Install `core + dev` on UEFI VM with ext4 + LUKS.
3. Validate first boot session health:
   - Hyprland starts, Waybar visible, dunst active, networking up.
4. Validate user shell/profile setup:
   - zsh default setup and prompt configuration functional.
5. Validate bundle integrity:
   - selected bundles installed; non-selected bundles absent.
6. Upgrade/sync sanity:
   - fresh install can run package updates without broken dependencies.
7. Laptop behavior smoke tests:
   - lid close/open, brightness control presence, external monitor reconnect behavior.

## Expected Challenges And Mitigations
- Calamares + Arch custom integration complexity:
  - mitigate by starting from known Arch/Calamares reference configs and incremental module enablement.
- AUR reliability for general users:
  - mitigate with curated AUR list, fallback alternatives, and documented break/fix policy.
- GPU divergence (especially NVIDIA):
  - mitigate with conditional config fragments and explicit “experimental” label until tested matrix expands.
- Long-term maintenance burden:
  - mitigate with quarterly cadence, tight supported hardware statement, and small initial bundle scope.
- Legal/licensing and redistributed assets:
  - audit all themes/assets/licenses before ISO publication and replace where redistribution is unclear.

## Assumptions And Defaults Chosen
- Target artifact: custom Arch ISO (not standalone independent distro repo stack in v1).
- Audience: general desktop users.
- Installer UX: Calamares GUI.
- Hardware strategy: laptop-first.
- Package strategy: Arch repos + AUR enabled broadly.
- Release cadence: quarterly stable.
- Storage default: ext4 with optional LUKS.
- Boot target: systemd-boot on UEFI.
- Architecture: x86_64 only for v1.
- Secure Boot: not supported in v1 unless explicitly added later.
