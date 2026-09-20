# Archinstall Desktop Profile

## Status

done

## Outcome

Archie should be available as an `Archie` option under Archinstall's guided
`Desktop` profile selection when the stock Arch Linux ISO starts Archinstall
with Archie's supported plugin URL. Selecting it should produce a single-user
Archie installation that is ready to use after the first reboot without
forking, patching, or replacing Archinstall.

## Decision Changes

- Integrate through Archinstall's documented Python plugin mechanism and load
  it with `archinstall --plugin-url <url>` from the stock Arch Linux ISO.
- Register Archie as a `ProfileType.DesktopEnv` so it appears alongside the
  existing desktop choices rather than as a separate installer or top-level
  profile type.
- Keep Archinstall responsible for disks, encryption, bootloader, kernels,
  networking, locale, users, graphics drivers, the greeter, official package
  installation, and service enablement.
- Keep Archie responsible for its package selection, AUR package build and
  installation flow, persistent checkout, Stow deployment, copy-managed files,
  shared store initialization, shell setup, and Archie-specific defaults.
- Keep the shared package manifest authoritative for required official packages,
  required AUR packages, build dependencies, and optional feature packages.
- Build required AUR packages in manifest order and append enabled optional
  feature packages without maintaining a separate dependency or output matrix.
- Require exactly one administrative user in the Archinstall configuration and
  deploy Archie only for that user.
- Complete provisioning before Archinstall exits so the installed system is
  ready after reboot; do not defer required work to a first-login service.
- Build AUR packages as the target user without passwordless sudo, then install
  only the completed package artifacts as root. Do not grant temporary
  `NOPASSWD: ALL` access to accommodate an AUR helper.
- Publish user-facing plugin URLs against immutable Archie release tags. A
  branch URL may exist for development but is not the documented installation
  path.
- Preserve `scripts/install.sh` as the existing-system, recovery, and manual
  onboarding path while extracting shared package and deployment behavior from
  it.
- Keep the Archinstall provisioner under `archinstall/`; it assumes a fresh
  target and fails on deployment conflicts rather than creating backups.
- Pass only the selected username through the bootstrap and provisioning
  boundaries; derive the target home, UID, and GID inside the installed system.
- Leave the completed historical
  [`vm-image-01-archinstall`](./vm-image-01-archinstall.md) work item unchanged;
  this work is the active stock-ISO integration path.

## Upstream Contract

Archinstall supports local and remote plugins through `--plugin` and
`--plugin-url`, and supports package entry-point discovery for custom images.
The stock-ISO flow in this work item uses `--plugin-url` so Archie can extend a
normal Archinstall release without maintaining an ISO.

The plugin should use only public Archinstall profile concepts needed to add a
desktop profile:

- a module-level `Plugin` entry point accepted by Archinstall's plugin loader
- `profile_handler.add_custom_profiles()` for registration
- a `Profile` subclass with `ProfileType.DesktopEnv`
- `DisplayServerType.Wayland` and `GreeterType.Sddm`
- `packages`, `services`, `install()`, `post_install()`, and `provision()` as
  appropriate for the installed Archinstall version
- `Installer.arch_chroot()` or another supported `Installer` operation for
  commands that must execute inside the target system
- Keep the plugin responsible for profile registration and argument passing;
  execute repository checkout through the static commit-pinned
  `archinstall/bootstrap.sh` script rather than generating shell code in Python.
- Keep `archinstall/provision.sh` responsible for Archie provisioning after
  the bootstrap checkout is complete.

Archinstall explicitly treats AUR packages as unsupported by the core project.
The Archie plugin therefore owns this unsupported boundary, must not imply that
upstream Archinstall supports those packages, and must fail with enough context
to distinguish an Archie/AUR failure from a base Archinstall failure.

References:

- [Archinstall Python plugins](https://archinstall.archlinux.page/archinstall/plugins.html)
- [Archinstall AUR support statement](https://archinstall.archlinux.page/help/known_issues.html#aur-packages)

## Scope Notes

The supported first version targets an online x86_64 UEFI installation from a
current official Arch Linux ISO. Archinstall remains free to offer its normal
disk layouts, filesystems, encryption, kernels, bootloaders, network choices,
and open-source graphics drivers unless a concrete incompatibility is found
during implementation.

Archie remains intended for a single personal-device user. The profile must
reject zero or multiple administrative users with a clear error rather than
silently selecting one. This validation occurs before Archie-specific user
deployment; if the Archinstall lifecycle does not expose users early enough to
reject the configuration before base installation, document that limitation
and fail at the earliest supported hook.

The profile should default to the current quickstart behavior:

- SDDM with the Archie theme enabled
- lid-close and power-button confirmation configuration enabled
- `p10k-lean` selected
- Adwaita dark configuration deployed
- custom XKB configuration disabled
- Nvidia system overrides enabled only when they agree with Archinstall's
  selected graphics-driver configuration

The profile must not guess monitor geometry, wallpaper mappings, brightness
devices, or `AQ_DRM_DEVICES`. It should create the existing machine-local
templates and preserve the documented post-install hardware review.

Session-dependent commands such as `gsettings` must not be treated as having
succeeded in the installation chroot. Prefer deployed settings where possible
and retain a concise first-session follow-up for settings that require a live
user D-Bus session.

## Main Quests

### Define shared package data

- Introduce one machine-readable package manifest consumed by both the existing
  quickstart and the Archinstall integration.
- Classify each package as an official runtime package, AUR runtime package,
  build dependency, or optional feature package.
- Include the packages currently supplied by Archinstall's Hyprland profile so
  the Archie profile does not import, mutate, or depend on an internal instance
  of that profile.
- Keep required AUR packages in manifest order, with optional feature packages
  selected only when their feature is enabled.
- Make package resolution fail before deployment when a required package is
  unavailable.

### Separate installation and deployment phases

- Refactor `scripts/install.sh` so package installation, root deployment, user
  deployment, store initialization, service setup, and session preferences have
  reusable boundaries.
- Keep the current interactive quickstart interface and defaults working.
- Add a noninteractive provisioning entry point intended to run as root inside
  an Archinstall target system.
- Require that entry point to receive the target username explicitly; derive
  the target home, UID, and GID from that installed account rather than root's
  `$USER` or `$HOME`.
- Run home and checkout operations with the target user's UID and GID, while
  keeping system paths and package installation root-owned.
- Preserve optional-package, Stow, copy-deployment, local-template scaffolding,
  shared-store, and service semantics. Keep conflict backups exclusive to the
  existing-system quickstart; fail fresh-target provisioning on conflicts.
- Set the user's login shell directly during provisioning instead of relying on
  the interactive `chsh` prompt.
- Ensure partial failures return a nonzero status and identify the failed phase
  without reporting the Archinstall run as successful.

### Implement the plugin and desktop profile

- Add a dedicated Archinstall plugin module with a valid `Plugin` entry point.
- Register one uniquely named `Archie` desktop profile at plugin load time.
- Declare Wayland, graphics-driver support, SDDM as the default greeter, the
  official package set, and required services through Archinstall's profile
  API.
- Declare and enforce the supported Archinstall version range with a readable
  compatibility error.
- Validate that exactly one Archinstall user has administrative privileges.
- Clone Archie to a persistent path under that user's home and check out the
  immutable tag or commit associated with the loaded plugin.
- Refuse a plugin/repository revision mismatch rather than installing moving or
  unreviewed code under the identity of a released plugin.
- Invoke the noninteractive provisioning entry point through the supported
  Archinstall target-system interface.
- Ensure that all Stow links resolve to the persistent checkout after `/mnt` is
  no longer mounted.

### Build and install AUR packages

- Prepare AUR build directories owned by the target user inside the installed
  system.
- Obtain and build each required AUR package as that user without allowing the
  build process to invoke privileged package installation.
- Install resulting package artifacts in a separate root-controlled step using
  `pacman -U`.
- Verify the primary artifact name and package metadata before root
  installation; do not install arbitrary files discovered in a writable build
  directory.
- Clean temporary build directories after success and preserve actionable logs
  after failure.
- Record the AUR package names and source revisions in Archie installation
  metadata or logs so an installed system can be audited later.
- Do not use the existing unattended `yay --noconfirm` path from the target
  user's account if it requires passwordless sudo.

### Publish a stable launch path

- Publish the plugin at a raw URL available from each Archie release tag.
- Document the exact stock-ISO command using an immutable release URL:

  ```bash
  archinstall --plugin-url https://gitlab.com/gabriel.chamon/archie/-/raw/<release>/archinstall/plugin.py
  ```

- Support pre-release VM testing from a feature branch by resolving the branch
  to one full commit SHA when the plugin loads, then use that SHA for the
  manifest, bootstrap script, and repository checkout.

- Add release validation that the documented plugin URL, configured ref, and
  repository assets agree.
- Document network requirements, the AUR trust boundary, the single-admin-user
  restriction, supported Archinstall versions, profile defaults, log locations,
  and machine-specific follow-up.
- Update the full installation guide to make this the preferred fresh-install
  path while retaining quickstart for an already installed Arch system.

### Verify the installed desktop

- Add unit tests for plugin registration, profile metadata, package selection,
  version checks, revision checks, and administrative-user validation.
- Test generated chroot commands, ownership transitions, primary AUR artifact
  validation, and deployment arguments without modifying the development host.
- Add tests ensuring the existing quickstart and the profile resolve the same
  package and feature defaults from the shared manifest.
- Run Python tests, Ruff, Pyright, and ShellCheck for changed code.
- Perform a destructive installation test in a disposable UEFI QEMU VM using a
  stock Arch Linux ISO and the configured plugin URL.
- Verify first boot reaches SDDM and a working Archie Hyprland session.
- Verify Waybar, Dunst, networking, audio, keyring integration, Archie store
  access, the login shell, enabled services, and deployed system files.
- Verify all Stow links remain valid after reboot and resolve into the target
  user's persistent checkout.
- Reboot a second time to catch dependencies on the live ISO, `/mnt`, temporary
  build paths, or the installation environment.
- Verify that a fresh target with an unexpected deployment conflict fails
  provisioning rather than moving existing files aside.

## Acceptance Criteria

- The documented command runs the stock Archinstall guided interface with an
  `Archie` choice under `Profile > Desktop` without modifying Archinstall or
  building a custom ISO.
- The plugin rejects unsupported Archinstall versions before destructive Archie
  provisioning begins.
- Selecting Archie with exactly one administrative user completes installation
  without an interactive Archie prompt or first-login finalizer.
- Configurations with zero or multiple administrative users fail with a clear
  explanation of the single-user requirement.
- Official packages are installed through Archinstall's supported package path.
- Required AUR packages are built without root or passwordless sudo and only
  validated package artifacts cross into the root installation step.
- The repository checkout and plugin use the same resolved immutable revision,
  and deployed Stow links survive unmounting and reboot.
- No required deployment step relies on a graphical session, user D-Bus, the
  live ISO filesystem, or an active `/mnt` mount after installation.
- First boot presents SDDM and the selected user can enter a usable Archie
  Hyprland session with the expected bar, notifications, shell, services, and
  shared Archie store.
- Machine-specific files are scaffolded without fabricated hardware values and
  the remaining review is documented clearly.
- The existing quickstart remains functional for already installed Arch systems
  and shares package/deployment definitions with the Archinstall path.
- Automated checks pass, and the two-reboot disposable-VM installation test is
  recorded with the tested Arch ISO and available installation details.

## Implementation Notes

- The first implementation targets Archinstall `>=4.4,<4.5`, matching the
  current stock ISO contract. The plugin resolves its configured release tag or
  development branch to one full commit SHA and uses that revision for the
  manifest, bootstrap script, and checkout. Run
  `scripts/release/verify-archinstall-plugin.sh` before publishing a release
  plugin.
- Archinstall 4.4 creates configured users before calling a selected profile's
  `provision()` hook, but after base and official profile package installation.
  Archie therefore rejects zero or multiple administrative users before any
  Archie checkout, AUR build, or deployment, while base Archinstall work has
  already occurred.

## Verification Record

- Result: successful disposable UEFI VM installation, first boot, and second
  reboot.
- Arch ISO: `/home/gchamon/Downloads/archlinux-2026.09.01-x86_64.iso`.
- Workflow: `templates/dev-env/archinstall/README.md`, using the development
  plugin URL for `feature/archinstall-desktop`.
- Archinstall configuration schema: `4.4`.
- Resolved Archie commit: unavailable after the test.
- Installed Archinstall version: unavailable after the test.
- Installed package revisions: unavailable after the test.
- Installation log: unavailable after the test.
- Automated validation: 202 Python tests passed; Ruff, Pyright, Bash syntax,
  manifest JSON, and diff checks passed. ShellCheck was unavailable in the
  validation environment.

## Metadata

### id

archinstall-integration-01
