# Arch Linux Integration Architecture

<!--toc:start-->

- [Arch Linux Integration Architecture](#arch-linux-integration-architecture)
  - [Purpose And Scope](#purpose-and-scope)
  - [Integration Overview](#integration-overview)
    - [Fresh Installation](#fresh-installation)
    - [Existing-System Deployment](#existing-system-deployment)
    - [AUR Publication](#aur-publication)
  - [Archinstall Boundary](#archinstall-boundary)
    - [Archinstall Responsibilities](#archinstall-responsibilities)
    - [Archie Responsibilities](#archie-responsibilities)
    - [Archinstall APIs](#archinstall-apis)
  - [Plugin And Revision Chain](#plugin-and-revision-chain)
    - [Remote Plugin](#remote-plugin)
    - [Revision Resolution](#revision-resolution)
    - [Profile Registration](#profile-registration)
    - [Bootstrap Handoff](#bootstrap-handoff)
  - [Internal Provisioning Chain](#internal-provisioning-chain)
    - [Persistent Checkout](#persistent-checkout)
    - [Root Phase](#root-phase)
    - [Target-User Phase](#target-user-phase)
    - [Persistent Outputs](#persistent-outputs)
  - [Shared Package Manifest](#shared-package-manifest)
  - [AUR Installation Boundary](#aur-installation-boundary)
  - [Archie CLI Package](#archie-cli-package)
    - [Python Build](#python-build)
    - [Arch Package Contents](#arch-package-contents)
    - [System Integration](#system-integration)
    - [Local Package Build](#local-package-build)
  - [AUR Recipe Publication](#aur-recipe-publication)
    - [Channels](#channels)
    - [Recipe Preparation](#recipe-preparation)
    - [AUR Handoff](#aur-handoff)
    - [What AUR Receives](#what-aur-receives)
  - [Arch Linux Contact Matrix](#arch-linux-contact-matrix)
  - [Trust And Privilege Boundaries](#trust-and-privilege-boundaries)
  - [Logging And Failure Boundaries](#logging-and-failure-boundaries)
  - [Known Gaps](#known-gaps)
  - [Change-Impact Checklist](#change-impact-checklist)
  - [Source Index](#source-index)
  - [Related Documentation](#related-documentation)
<!--toc:end-->

## Purpose And Scope

This document describes Archie's implemented points of contact with Arch Linux:

- the stock-ISO [Archinstall](https://archinstall.archlinux.page/) plugin;
- the internal bootstrap and provisioning scripts that turn an Archinstall
  target into an Archie system;
- official repository and AUR package installation;
- the `archie-cli` Arch package and its system integration;
- GitLab CI publication of stable and prerelease recipes to the AUR.

It is an architecture and maintenance guide. User-facing commands remain in the
[installation guide](../user/GUIDE.md) and
[quickstart](../user/QUICKSTART.md). The proposed custom Arch ISO and Calamares
installer are a separate, future architecture documented in
[DISTRO.md](./DISTRO.md).

## Integration Overview

Archie has three related but distinct flows.

### Fresh Installation

```text
Arch Linux ISO
  -> Archinstall downloads archinstall/plugin.py
  -> plugin resolves a branch or release tag to one commit SHA
  -> plugin fetches package-manifest.json and bootstrap.sh at that SHA
  -> Archinstall installs the base system and official profile packages
  -> plugin stages bootstrap.sh inside the target and enters arch-chroot
  -> bootstrap creates a detached, user-owned ~/archie checkout
  -> archinstall/provision.sh builds yay-bin and the remaining AUR packages, then deploys Archie
  -> Archie CLI initializes shared state and services
```

### Existing-System Deployment

```text
Existing Arch Linux system
  -> docs/user/QUICKSTART.md downloads scripts/install.sh
  -> install.sh installs bootstrap packages and yay
  -> yay installs archie-cli
  -> archie initializes shared state
  -> install.sh reads the shared package manifest
  -> pacman and yay install the remaining official and AUR packages
  -> Stow deploys system and user configuration
```

The two installation paths share package and deployment definitions, but they
do not share the same AUR privilege model. Quickstart bootstraps and uses
`yay`; Archinstall builds `yay-bin` and the remaining AUR packages as the
selected user, then reserves package installation for root. Archinstall does
not use the newly installed `yay` to install the other packages.

### AUR Publication

```text
GitLab pipeline
  -> select stable, RC, or alpha channel
  -> clone the matching AUR Git repository over SSH
  -> render PKGBUILD from a repository template
  -> pin the Archie source commit
  -> regenerate and verify .SRCINFO
  -> commit and push PKGBUILD plus .SRCINFO to AUR
  -> AUR consumers build the Arch package locally
```

This flow publishes source recipes, not prebuilt `.pkg.tar.zst` files.

## Archinstall Boundary

### Archinstall Responsibilities

Archinstall remains responsible for:

- disk layout, filesystems, encryption, and mounting;
- the bootloader and kernels;
- locale, timezone, hostname, and networking;
- user creation and sudo status;
- graphics-driver selection;
- installation of official repository packages declared by the profile;
- greeter installation and its normal guided-install lifecycle.

Archie's profile runs after Archinstall has created users and installed the
profile's official packages. A provisioning error can therefore fail after the
base system has already been written.

### Archie Responsibilities

Archie owns:

- validation of the supported Archinstall version and administrative-user
  model;
- the desktop profile's package and service defaults;
- resolution of the Archie source revision;
- the persistent repository checkout;
- the unsupported-by-Archinstall AUR boundary;
- system and home configuration deployment;
- Archie store initialization and Archie-specific service defaults.

The supported profile contract is currently Archinstall 4.4.x, online x86_64
UEFI installation, and exactly one administrative user.

### Archinstall APIs

[`archinstall/plugin.py`](../../archinstall/plugin.py) is self-contained because
Archinstall downloads it before the rest of the repository exists. It uses:

- `Profile`, `ProfileType.DesktopEnv`, and `profile_handler`;
- `DisplayServerType.Wayland` and `GreeterType.Sddm`;
- `archinstall.lib.version.get_version()`;
- `archinstall.lib.log.info()`;
- profile constructor fields for packages, services, graphics-driver support,
  and display server;
- user objects exposing `username` and `sudo`;
- `install_session.target` for host-side writes into the mounted target;
- `install_session.arch_chroot()` for target-side execution.

The version guard in the plugin is part of this API contract. A supported-range
change must be tested against upstream Archinstall before it is broadened.

## Plugin And Revision Chain

### Remote Plugin

Users launch the release plugin from an immutable tag. Development testing uses
the moving `feature/archinstall-desktop` branch. The initial plugin download is
trusted through the selected HTTPS GitLab URL; no second Archie signature is
applied to that Python file.

`ARCHIE_RELEASE` selects release mode. When it is `None`,
`ARCHIE_DEVELOPMENT_REF` supplies the feature branch.

### Revision Resolution

The plugin resolves the configured branch or tag through the GitLab commits API
once during initialization. It validates the returned value as a full
40-character lowercase commit SHA and then uses that SHA for:

- `archinstall/package-manifest.json`;
- `archinstall/bootstrap.sh`;
- the target's persistent Git checkout.

This prevents those inputs from drifting relative to one another during an
installation. Development remains intentionally branch-based at entry; release
reproducibility depends on the release tag being immutable.

### Profile Registration

The plugin validates the manifest and registers `ArchieProfile` with:

- official runtime and build-dependency packages;
- Wayland as the display server;
- SDDM as the default greeter;
- graphics-driver support;
- Bluetooth and power-profiles-daemon services.

The resolved revision is stored on the profile instance so provisioning uses
the same snapshot that supplied its manifest and bootstrap script.

### Bootstrap Handoff

The profile requires exactly one sudo-enabled Archinstall user. It derives the
home as `/home/<username>`, writes the fetched bootstrap to
`/root/archie-bootstrap.sh` in the target, sets mode `0700`, and invokes it with
an argument-only command built by `shlex.join()`.

The bootstrap receives:

- repository URL;
- resolved commit SHA;
- target username;
- and derives the target home from the username.

The script is staged outside `/tmp` because Archinstall 4.4 uses systemd-backed
`arch-chroot -S`, whose temporary-directory namespace does not expose a
host-staged target `/tmp` reliably. The plugin removes the bootstrap in a
`finally` block.

## Internal Provisioning Chain

### Persistent Checkout

[`archinstall/bootstrap.sh`](../../archinstall/bootstrap.sh) runs as root in the
target but performs Git operations as the selected user. It:

1. validates the repository, revision, username, and root execution;
2. resolves the user's UID and GID;
3. creates `~/archie` when absent;
4. fetches and checks out the exact resolved SHA in detached mode;
5. rejects an existing checkout at a different revision;
6. invokes `archinstall/provision.sh` from the checkout.

The checkout persists after installation and is the source tree behind many GNU
Stow links.

### Root Phase

[`archinstall/provision.sh`](../../archinstall/provision.sh) receives the
selected username and derives its home, UID, and GID from the installed
account before doing privileged work.

The root phase:

- creates user-owned cache directories used by AUR builds;
- appends output to `/var/log/archie/provision.log`;
- builds and installs AUR packages through the split described below;
- Stow-deploys `etc`, the SDDM theme, and optional Nvidia configuration;
- copies logind files that cannot remain home-backed symlinks;
- creates the `archie` group and adds the selected user;
- runs `archie system initialize-store` as the selected user;
- enables Bluetooth, power-profiles-daemon, and SDDM;
- changes the selected user's shell to zsh.

The provisioner sources deployment primitives from
[`lib/bash/lib.sh`](../../lib/bash/lib.sh). Quickstart and Archinstall
therefore share Stow, template-scaffolding, and feature-default logic without
sharing package-install privilege behavior. The provisioner assumes a fresh
target; an unexpected deployment conflict fails provisioning rather than being
backed up. Quickstart retains its existing-system backup behavior.

### Target-User Phase

The root process re-executes `provision.sh --user-phase` through
`runuser`, with explicit `HOME` and `USER`. This phase:

- deploys `home`, `config`, `local`, and `p10k-lean` Stow packages;
- scaffolds machine-local files without inventing hardware values;
- creates required home directories such as `~/Pictures/Screenshots`.

### Persistent Outputs

Important outputs include:

- `~/archie`: detached persistent source checkout;
- `/var/log/archie/provision.log`: provisioning output and AUR source revisions;
- `/var/lib/archie/store.sqlite3`: shared Archie policy store;
- `/var/lib/archie/waybar/`: active shared Waybar state;
- `~/.cache/archie/aur`: AUR workspace parent and failed-build evidence;
- Stow-managed user and system files;
- machine-local Hyprland, wallpaper, and shell override files.

## Shared Package Manifest

[`archinstall/package-manifest.json`](../../archinstall/package-manifest.json)
is the shared package contract.

| Field | Meaning | Consumers |
| --- | --- | --- |
| `official_runtime` | Official repository runtime packages | Archinstall profile and quickstart |
| `aur_runtime` | Required runtime packages sourced from AUR | Manifest validation, quickstart, and Archinstall provisioner |
| `build_dependencies` | Official packages needed for AUR builds | Archinstall profile and quickstart |
| `optional_features` | AUR packages associated with optional features | Quickstart and Archinstall provisioners |

The Archinstall provisioner iterates required `aur_runtime` packages in manifest
order, then appends the `sddm_theme` packages when that feature is enabled.
Package classification and optional-feature changes must therefore be reviewed
together.

## AUR Installation Boundary

Archinstall itself does not support AUR packages. Archie owns this extension and
keeps build and installation privileges separate.

Before building AUR packages, the provisioner deploys Archie’s
`/etc/makepkg.conf.d/archie.conf` override, which disables debug package
generation. For every required or enabled optional AUR package, it then:

1. clones or updates `https://aur.archlinux.org/<package>.git` as the target
   user;
2. records the AUR Git revision in the provisioning log;
3. runs `makepkg --nodeps --nocheck --noconfirm --cleanbuild` as that user;
4. obtains artifact paths from `makepkg --packagelist`;
5. rejects symlinks, paths outside the build directory, and invalid files;
6. reads the embedded package name with `pacman -Qpq` as root and requires one
   non-debug artifact matching the source package;
7. installs the validated artifact with root `pacman -U --noconfirm`;
8. removes successful build directories while preserving failed ones.

`makepkg --install` is deliberately not used. AUR build code executes without
passwordless sudo, while package installation remains a root-controlled step.

## Archie CLI Package

### Python Build

[`pyproject.toml`](../../pyproject.toml) defines the `archie` Python distribution
and the `archie = archie.cli:main` console entry point. `uv_build` produces the
wheel from `src/archie` and includes the application assets, CSS, and Waybar
themes declared in the build configuration.

### Arch Package Contents

The AUR templates are:

- [`PKGBUILD.aur`](../../packaging/archie-cli/PKGBUILD.aur) for `archie-cli`;
- [`PKGBUILD.nightly.aur`](../../packaging/archie-cli/PKGBUILD.nightly.aur) for
  `archie-cli-nightly`.

Each recipe:

1. fetches the Archie repository at an exact commit;
2. rewrites the project version to the channel's `pkgver`;
3. builds a wheel with `uv build`;
4. stages it with `python -m installer`;
5. adds the license and user documentation;
6. adds zsh completion;
7. adds sysusers and tmpfiles declarations.

Stable and nightly packages both provide `archie`, conflict with the legacy
`archie` package, and conflict with one another.

### System Integration

[`archie.sysusers`](../../packaging/archie-cli/archie.sysusers) declares the
system `archie` group. [`archie.tmpfiles`](../../packaging/archie-cli/archie.tmpfiles)
declares the group-writable shared state under `/var/lib/archie`, including the
SQLite store and Waybar directory.

The package has no custom install script. Standard pacman/systemd hooks process
the sysusers and tmpfiles declarations. Installation flows still call
`archie system initialize-store` to create and migrate application-level state.

### Local Package Build

[`packaging/archie-cli/PKGBUILD`](../../packaging/archie-cli/PKGBUILD) builds the
current checkout rather than fetching a remote commit.
[`scripts/install-archie-cli.sh`](../../scripts/install-archie-cli.sh) wraps this
with `makepkg -Cfsi --noconfirm` for development and manual installation.

## AUR Recipe Publication

### Channels

The `publish-archie-cli` GitLab job defines three channels:

| Channel | Trigger | AUR package | Derived version |
| --- | --- | --- | --- |
| stable | Default branch pipeline | `archie-cli` | Project version |
| RC | `develop` pipeline | `archie-cli-nightly` | Project version plus `rc` |
| alpha | Merge request targeting the default branch | `archie-cli-nightly` | Project version plus `a` |

The scripts also accept `nightly` as an alpha-style marker, but the current CI
matrix does not schedule a periodic nightly job. The nightly AUR repository is
therefore a shared prerelease channel, not necessarily a daily build.

### Recipe Preparation

[`prepare-archie-cli-aur.sh`](../../scripts/release/prepare-archie-cli-aur.sh):

- requires a full source commit SHA;
- reads the stable base version from `pyproject.toml`;
- selects the stable or nightly PKGBUILD template;
- derives channel-specific `pkgver`;
- increments stable `pkgrel` when the version is unchanged but the source commit
  changes;
- uses the pipeline IID as prerelease `pkgrel` when supplied;
- pins `_commit` in the rendered recipe;
- regenerates `.SRCINFO` with `makepkg --printsrcinfo`.

[`verify-archie-cli-package.sh`](../../scripts/release/verify-archie-cli-package.sh)
checks the expected version, positive package release, full commit pin, VCS
source expression, `SKIP` checksum declaration, and exact `.SRCINFO` agreement.

### AUR Handoff

The GitLab job runs in `archlinux:base-devel`. Root installs CI tools, creates an
unprivileged `aur-builder` account, and installs the AUR SSH key from the
protected `AUR_SSH_PRIVATE_KEY_B64` variable.

All AUR Git operations and release scripts then run as `aur-builder`. CI clones:

- `ssh://aur@aur.archlinux.org/archie-cli.git`; or
- `ssh://aur@aur.archlinux.org/archie-cli-nightly.git`.

[`publish-archie-cli.sh`](../../scripts/release/publish-archie-cli.sh) stages only
`PKGBUILD` and `.SRCINFO`, commits them, and pushes `HEAD:master` to AUR.

### What AUR Receives

AUR receives a Git repository containing the package recipe and metadata. It
does not receive:

- a prebuilt wheel;
- a prebuilt Arch package;
- Archie's source tree copied into the AUR repository.

An AUR client clones the recipe. `makepkg` then fetches the exact Archie commit,
builds the wheel, and creates the Arch package on the consumer's machine.

## Arch Linux Contact Matrix

| Arch Linux surface | Archie contact point | Purpose |
| --- | --- | --- |
| Official ISO | `archinstall --plugin-url` | Load the remote desktop profile |
| Archinstall Python API | `archinstall/plugin.py` | Register profile and provision target |
| Official package repositories | Profile packages and quickstart `pacman` | Install supported packages and build tools |
| `arch-chroot -S` | `install_session.arch_chroot()` | Enter the installed target |
| AUR Git | `aur.archlinux.org/<package>.git` | Retrieve PKGBUILDs for local builds |
| `makepkg` | Provisioner and AUR consumers | Build Arch package artifacts |
| pacman query API | `pacman -Qpq` | Validate artifact package identity |
| pacman local install API | `pacman -U` | Install validated AUR artifacts |
| AUR SSH Git | GitLab deploy job | Publish CLI recipes and `.SRCINFO` |
| sysusers.d | `archie.sysusers` | Declare the shared `archie` group |
| tmpfiles.d | `archie.tmpfiles` | Declare shared state paths and permissions |
| systemd | Profile and provisioner services | Enable desktop-related services |
| GNU Stow | `scripts/install.sh` helpers | Deploy repository-owned configuration |

## Trust And Privilege Boundaries

- **Initial plugin:** privileged Python downloaded from the operator-selected
  GitLab URL. Releases should use immutable tags.
- **Resolved snapshot:** branch or tag resolution happens once; manifest,
  bootstrap, and checkout then share one SHA.
- **Bootstrap:** staged in target `/root`, mode `0700`, and run as root through
  Archinstall.
- **Persistent checkout:** created and owned by the target user, but supplies
  deployment content later consumed by privileged provisioning.
- **AUR source:** PKGBUILDs and their source code are external, moving inputs.
- **AUR build:** runs as the target user without passwordless sudo.
- **Artifact installation:** root validates identity and calls `pacman -U`.
  Pacman package hooks and package contents consequently become privileged
  inputs.
- **AUR publication:** CI root provisions tools and credentials; the dedicated
  `aur-builder` user performs Git and release-script operations.
- **Shared runtime state:** sysusers/tmpfiles and group membership mediate access
  to `/var/lib/archie`.

## Logging And Failure Boundaries

`/var/log/archie/provision.log` begins after `provision.sh` starts. It
captures stdout and stderr, deployment phases, AUR source revisions, and the
privileged commands emitted by `run_sudo_cmd`. It is not a complete command
transcript; target-user command invocations are not printed consistently.

Failures before that point, including plugin loading, GitLab API access,
bootstrap validation, and persistent checkout creation, remain in Archinstall's
output and logs. Failed AUR build directories remain under
`~/.cache/archie/aur` for inspection. The staged bootstrap is removed even when
provisioning fails.

Package publication has separate failure boundaries:

- recipe preparation can reject invalid versions, commits, or channels;
- recipe verification can reject metadata drift;
- AUR publication can fail at SSH authentication, Git commit, or push;
- consumer builds can still fail after a valid recipe is published.

## Known Gaps

These are current limitations, not promises of completed mitigation.

- The persistent checkout is user-owned, while root later executes provisioning
  scripts and deploys system content from its working tree. Commit identity is
  checked, but working-tree cleanliness and origin identity are not.
- AUR repository revisions are logged but not pinned in the shared manifest.
- Artifact validation and `pacman -U` operate on files in a user-writable build
  directory, leaving a validation-to-install race boundary.
- Archinstall AUR builds use `--nocheck`, so PKGBUILD `check()` functions are
  skipped.
- `pyproject.toml` declares Pillow and PyGObject dependencies, while the current
  PKGBUILD runtime dependency arrays declare only Python and SQLite. The Python
  and Arch dependency models need reconciliation.
- AUR PKGBUILDs use a Git source but do not currently list `git` in
  `makedepends`. Controlled CI and Archinstall paths install Git independently.
- The GitLab publication job verifies recipes but does not perform a clean full
  AUR package build and installation smoke test. The Python test jobs are not a
  universal publication gate for every RC or alpha pipeline.
- Archinstall integration tests primarily mock Python boundaries or inspect
  shell source. Destructive stock-ISO VM and first-boot validation remains a
  manual acceptance boundary.

## Change-Impact Checklist

| Change | Also review |
| --- | --- |
| Archinstall API or supported version | `plugin.py`, integration tests, GUIDE, release verifier |
| Development branch or release ref model | Plugin URLs, GitLab API calls, bootstrap arguments, verifier |
| Official or AUR package set | Manifest categories, dependency ordering, quickstart, profile tests |
| AUR build behavior | Provisioner privilege split, artifact checks, logging, VM acceptance test |
| User/system deployment | `install.sh`, provisioner phases, Stow ADR, backup behavior |
| Python runtime dependency | `pyproject.toml`, all PKGBUILDs, manifest, package tests |
| CLI package payload | Wheel includes, PKGBUILDs, sysusers/tmpfiles, completion, docs |
| Stable/prerelease versioning | Prepare/verify scripts, GitLab matrix, release-script tests |
| AUR repository or credentials | GitLab variables, SSH URLs, development documentation |
| Shared store path or permissions | tmpfiles, sysusers, CLI system code, migration behavior |

## Source Index

| Concern | Source |
| --- | --- |
| Archinstall profile | [`archinstall/plugin.py`](../../archinstall/plugin.py) |
| Shared package contract | [`archinstall/package-manifest.json`](../../archinstall/package-manifest.json) |
| Target bootstrap | [`archinstall/bootstrap.sh`](../../archinstall/bootstrap.sh) |
| Archinstall provisioner | [`archinstall/provision.sh`](../../archinstall/provision.sh) |
| Shared deployment helpers | [`lib/bash/lib.sh`](../../lib/bash/lib.sh) |
| Python package metadata | [`pyproject.toml`](../../pyproject.toml) |
| Store initialization command | [`src/archie/system.py`](../../src/archie/system.py) |
| Store path and SQLite lifecycle | [`src/archie/store/database.py`](../../src/archie/store/database.py) |
| Local Arch package | [`packaging/archie-cli/PKGBUILD`](../../packaging/archie-cli/PKGBUILD) |
| Stable AUR template | [`packaging/archie-cli/PKGBUILD.aur`](../../packaging/archie-cli/PKGBUILD.aur) |
| Prerelease AUR template | [`packaging/archie-cli/PKGBUILD.nightly.aur`](../../packaging/archie-cli/PKGBUILD.nightly.aur) |
| sysusers declaration | [`packaging/archie-cli/archie.sysusers`](../../packaging/archie-cli/archie.sysusers) |
| tmpfiles declaration | [`packaging/archie-cli/archie.tmpfiles`](../../packaging/archie-cli/archie.tmpfiles) |
| Recipe preparation | [`scripts/release/prepare-archie-cli-aur.sh`](../../scripts/release/prepare-archie-cli-aur.sh) |
| Recipe verification | [`scripts/release/verify-archie-cli-package.sh`](../../scripts/release/verify-archie-cli-package.sh) |
| AUR publication | [`scripts/release/publish-archie-cli.sh`](../../scripts/release/publish-archie-cli.sh) |
| Archinstall release verification | [`scripts/release/verify-archinstall-plugin.sh`](../../scripts/release/verify-archinstall-plugin.sh) |
| GitLab channel rules | [`.gitlab-ci.yml`](../../.gitlab-ci.yml) |
| Integration tests | [`tests/test_archinstall_integration.py`](../../tests/test_archinstall_integration.py) |
| Packaging tests | [`tests/test_packaging.py`](../../tests/test_packaging.py) |
| Release-script tests | [`tests/test_release_scripts.py`](../../tests/test_release_scripts.py) |

## Related Documentation

- [System installation guide](../user/GUIDE.md)
- [Quickstart](../user/QUICKSTART.md)
- [Development and repository hosting](../user/DEVELOPMENT.md)
- [Development environment](../development/DEV_ENV.md)
- [GNU Stow architecture decision](./decisions/0001-use-gnu-stow-for-config-deployment.md)
- [GitLab upstream architecture decision](./decisions/0002-use-gitlab-as-canonical-upstream-with-github-mirror.md)
- [Future custom distro plan](./DISTRO.md)
- [Archinstall integration work item](../work-items/archinstall-integration-01-desktop-profile.md)
