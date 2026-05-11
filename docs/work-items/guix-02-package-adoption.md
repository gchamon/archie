# Adopt Guix For User-Space Package Management

Migrate Archie's user-space package surface from the hardcoded
`pacman`/`yay` arrays in `scripts/install.sh` to a Guix manifest
governed by a commit-pinned `channels.scm` and a configurable
staleness floor. Stow remains the deployment mechanism for `$HOME`
and `/etc`; this work-item changes only how packages are installed,
not how configuration is deployed.

## Status

Planned

## Outcome

User-space packages with a Guix equivalent are installed via
`guix time-machine -C channels.scm -- package -m manifest.scm`,
gated by `ARCHIE_GUIX_ENABLED`. The pacman and yay invocations in
`scripts/install.sh` shrink to a documented residual set: bootstrap
(`base-devel`, `git`), hardware (kernel, firmware, drivers), and AUR
or `-bin`/`-git` packages with no Guix equivalent. The locally-defined
Guix recipes produced by `guix-01`'s POC are promoted into the repo
under `guix/packages/`. `docs/user/GUIDE.md` references the manifest
and a single helper invocation instead of a long `yay -S --needed`
block. Stow continues to own configuration deployment exactly as it
does today.

## Decision Changes

- User-space package management migrates from the hardcoded arrays in
  `scripts/install.sh` (lines 11-81) to `guix/manifest.scm`, mirroring
  the manifest-as-source-of-truth contract that
  `deployment-management-06` establishes for Stow. The two manifests
  coexist: one for packages, one for deployment.
- Staleness is enforced by pinning channel commits whose timestamps
  are at least `ARCHIE_GUIX_STALENESS_DAYS` days old via
  `guix time-machine -C channels.scm`. `guix pull` is forbidden.
- pacman and yay retain a minimum residual surface, documented in the
  manifest's prose header: `base-devel`, `git`, kernel, firmware,
  hardware drivers, `zen-browser-bin`, and any `-git` HEAD-tracking
  packages from the AUR partition produced in `guix-01`. The exact
  list comes from `guix-01`'s partition output.
- Locally-defined Guix recipes for niche desktop packages live under
  `guix/packages/` and are loaded via a custom channel declared in
  `guix/channels.scm`.
- `docs/user/GUIDE.md` ceases to list `yay -S --needed` blocks for any
  package present in `guix/manifest.scm`. The residual yay block is
  retained but trimmed to the residual surface and labeled as such.
- Stow and `deployment-management-06` are unaffected by this work-item.
  `$HOME` and `/etc` deployment continue to flow through Stow.
- `guix home` is **not** introduced in this work-item. That migration
  is `guix-03`'s responsibility.

## Dependencies

- [Work Item guix-01](guix-01-evaluation-and-poc.md) must produce a
  proceed recommendation, the package partition, and the validated
  recipe-maintenance approach before this work-item can execute.
- [Epic guix](../epics/guix.md) defines the staged adoption shape.
- `lib/bash/lib.sh:load_repo_env_file` is the env-loading hook the new
  `ARCHIE_GUIX_*` toggles plug into through `.env.sh`.

## Scope Notes

Included:

- Authoring `guix/channels.scm` (commit-pinned channels, including the
  custom Archie channel declaration), `guix/manifest.scm` (package
  list with self-describing residual-surface header), and
  `guix/packages/` (locally-defined recipes promoted from `guix-01`).
- A `scripts/guix-refresh-channels.sh` tool that walks each channel's
  upstream git history, picks the newest commit older than
  `ARCHIE_GUIX_STALENESS_DAYS`, and rewrites `guix/channels.scm`
  idempotently.
- A `scripts/guix-deploy.sh` thin wrapper that loads `.env.sh`, reads
  the manifest and channels file paths, and runs
  `guix time-machine -C channels.scm -- package -m manifest.scm`.
- A new `bootstrap_guix` step in `scripts/install.sh` analogous to
  `bootstrap_yay` (lines 219-247): installs Guix from the AUR, runs
  daemon setup, authorizes substitute keys. Gated by
  `ARCHIE_GUIX_ENABLED`.
- A new `deploy_guix_packages` step in `scripts/install.sh` that
  invokes `scripts/guix-deploy.sh`. Gated by `ARCHIE_GUIX_ENABLED`.
- Shrinking `ESSENTIAL_PACKAGES`, `ZSH_PACKAGES`, `THEME_PACKAGES`,
  and `KEYRING_PACKAGES` to the residual partition produced by
  `guix-01`. Array structure is preserved so the residual flows
  through `run_yay_install` unchanged.
- Adding `ARCHIE_GUIX_*` toggles to `.env.dist.sh`.
- Realigning `docs/user/GUIDE.md` to reference
  `guix/manifest.scm` and `scripts/guix-deploy.sh`. Removing
  `yay -S --needed` blocks for packages now in the manifest.

Not included:

- Anything Guix Home related. `$HOME` configuration deployment stays
  on Stow until `guix-03`.
- Any change to `deployment-packages/`, the Stow installer code path,
  or the manifest contract from `deployment-management-06`.
- Bootstrap-stage packages (`base-devel`, `git`), hardware packages,
  and the AUR residual surface. They stay on pacman/yay.
- `archinstall` and `scripts/create-arch-base-image.sh`. Pre-Guix
  bootstrap is unchanged.

## Main Quests

### 1. Promote the locally-defined recipes into the repo

Take the throwaway Guix package definitions from `guix-01`'s Quest 3
and promote them into `guix/packages/` as a maintainable Archie
channel. Define the channel layout (one file per package or one file
per package family — pick based on the recipe count from `guix-01`),
write a top-level `guix/packages/README.md` that names the upstream
sources and the maintenance contract, and declare the channel in
`guix/channels.scm` so `guix time-machine` picks it up.

### 2. Author the production manifest and channel pin

Write `guix/channels.scm` with commit pins for both the upstream Guix
channel and the local Archie channel. Each pin satisfies the staleness
floor as of the work-item's execution date. Write `guix/manifest.scm`
as a `specifications->manifest` list covering every package from the
upstream-Guix and locally-defined-recipe partitions in `guix-01`. Open
the manifest with a prose comment block enumerating the residual
pacman and yay surface so the partition is reviewable in one place.

### 3. Implement the channel-pin refresh tool

Write `scripts/guix-refresh-channels.sh` that:

- Reads each channel from `guix/channels.scm`.
- Walks the channel's upstream git history.
- Picks the newest commit whose committer timestamp is older than
  `ARCHIE_GUIX_STALENESS_DAYS`.
- Rewrites `guix/channels.scm` with the new pin.
- Produces a no-op (no file change, exit 0) when the existing pin
  still satisfies the threshold.

The tool is the only sanctioned mechanism for advancing the staleness
floor. `guix pull` remains forbidden.

### 4. Implement the installer integration and env contract

Refactor `scripts/install.sh`:

- Add `bootstrap_guix` analogous to `bootstrap_yay` (lines 219-247).
  Gated by `ARCHIE_GUIX_ENABLED`.
- Add `deploy_guix_packages` that invokes `scripts/guix-deploy.sh`.
  Gated by `ARCHIE_GUIX_ENABLED`.
- Shrink the four package arrays (lines 11-81) to the residual
  partition.
- Wire the new steps into the existing install order: bootstrap_yay
  remains for the residual surface and runs first; bootstrap_guix
  runs after; deploy_guix_packages runs after the residual yay
  install completes.

Add the following toggles to `.env.dist.sh`, with explanatory comments
in the same style as the existing `ARCHIE_ENABLE_*` block:

- `ARCHIE_GUIX_ENABLED` — master toggle. Default `0` until adoption
  is approved on a real workstation; `guix-01`'s recommendation
  decides the default for this work-item's initial commit.
- `ARCHIE_GUIX_STALENESS_DAYS` — staleness floor in days. Default
  `7`.
- `ARCHIE_GUIX_CHANNELS_FILE` — repo-relative path. Default
  `guix/channels.scm`.
- `ARCHIE_GUIX_MANIFEST_FILE` — repo-relative path. Default
  `guix/manifest.scm`.
- `ARCHIE_GUIX_PROFILE` — target profile path. Default
  `$HOME/.guix-profile`.

Toggles flow through `lib/bash/lib.sh:load_repo_env_file` exactly the
way the existing `ARCHIE_ENABLE_*` toggles do.

#### Side-quests

- Document the forbidden `guix pull` rule in `docs/user/GUIDE.md` and
  in the `guix/manifest.scm` header so operators do not silently
  break the staleness contract.
- Document the exact zsh init snippet required to source the Guix
  profile (`/etc/profile.d/guix.sh` or
  `$ARCHIE_GUIX_PROFILE/etc/profile`) so PATH integration works for
  every shell, not just login shells. The snippet ships through the
  existing Stow `home` package; this side-quest does not change Stow
  ownership.

### 5. Realign documentation and verify

Replace the `yay -S --needed` blocks in `docs/user/GUIDE.md` (sections
1.3 "Install Essential Packages with Yay" and 3.1 "Install Theme
Packages") with a reference to `guix/manifest.scm` and a single
`scripts/guix-deploy.sh` invocation. Retain a trimmed residual
`yay -S --needed` block labeled clearly as the residual AUR/bootstrap
surface.

Verify by:

- Running `scripts/install.sh` end to end on a clean disposable VM
  and confirming the resulting profile matches the pinned manifest.
- Running `scripts/guix-deploy.sh` standalone on an
  already-deployed system and confirming idempotency.
- Reproducing the same profile on two VMs from the same channel pin
  and manifest and diffing the resulting `~/.guix-profile/manifest`.
  The diff must be empty.
- Running `shellcheck` on `scripts/guix-deploy.sh`,
  `scripts/guix-refresh-channels.sh`, and the refactored
  `scripts/install.sh`.
- Confirming the existing Stow flow still works unchanged: every
  `deployment-packages/` package deploys exactly as it did before
  this work-item.

## Acceptance Criteria

- `guix/channels.scm`, `guix/manifest.scm`, and `guix/packages/`
  exist with a documented schema and a self-describing
  residual-surface header in the manifest.
- `scripts/install.sh` no longer references any package name in its
  package arrays that has a Guix equivalent listed in
  `guix/manifest.scm`.
- `scripts/guix-deploy.sh` and `scripts/guix-refresh-channels.sh`
  exist and are documented entrypoints.
- `.env.dist.sh` exposes `ARCHIE_GUIX_ENABLED`,
  `ARCHIE_GUIX_STALENESS_DAYS`, `ARCHIE_GUIX_CHANNELS_FILE`,
  `ARCHIE_GUIX_MANIFEST_FILE`, and `ARCHIE_GUIX_PROFILE`, all
  loaded through `lib/bash/lib.sh:load_repo_env_file`.
- `docs/user/GUIDE.md` references `guix/manifest.scm` and the deploy
  helper; no `yay -S --needed` block lists a package that also lives
  in `guix/manifest.scm`.
- The Stow flow defined by `deployment-management-06` is byte-for-byte
  unchanged in behavior. `deployment-packages/` is untouched.
- A clean-VM install reproduces the pinned package state, and a
  re-run of `scripts/guix-deploy.sh` is idempotent.

## Metadata

### id

guix-02
