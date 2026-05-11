# Adopt Guix Home For `$HOME` Configuration And Resolve Stow's `/etc` Residual

Migrate Archie's `$HOME` configuration deployment from the
Stow-managed `home`, `config`, `local`, and `p10k-*` packages to a
Guix Home configuration sourced from `guix/home-configuration.scm`,
and resolve the relationship between the new substrate and
`deployment-management-06`. Apply `guix-01`'s `/etc` strategy
recommendation to the residual privileged surface
(`etc`, `sddm-theme`, `lid-close`, `nvidia`, `xkb`).

## Status

Planned

## Outcome

`$HOME` configuration is owned by `guix home reconfigure` against
`guix/home-configuration.scm`. The Stow packages `home`, `config`,
`local`, `p10k-classic`, `p10k-lean`, `p10k-pure`, and `p10k-rainbow`
are retired from `deployment-packages/`. The privileged Stow packages
(`etc`, `sddm-theme`, `lid-close`, `nvidia`, `xkb`) follow the `/etc`
strategy recommendation produced by `guix-01`. `deployment-management-06`'s
manifest contract is either re-scoped to the residual surface or
retired, depending on the strategy. `docs/user/GUIDE.md` references
`guix home reconfigure` for `$HOME` and the chosen `/etc` mechanism
for system files.

## Decision Changes

- Guix Home becomes the canonical owner of `$HOME` configuration.
  Stow's user-side packages are retired. `guix home reconfigure`
  replaces `stow --dir deployment-packages --target "$HOME"` and its
  XDG and `~/.local` siblings.
- The `ARCHIE_P10K_PACKAGE` selector becomes a Scheme `cond` inside
  `home-configuration.scm`. The `.env.dist.sh` toggle name and
  default remain unchanged so user-facing UX does not regress.
- The `ARCHIE_ENABLE_*` toggles for the user-side surface (none today,
  but reserved for future per-package opt-ins) flow into Scheme
  conditionals at the top of `home-configuration.scm`.
- The privileged Stow packages follow `guix-01`'s `/etc` strategy
  recommendation. The candidates are: a thin Stow `/etc` adapter that
  retains the privileged half of `deployment-management-06`; a
  bespoke symlink farmer over a Guix-built profile that retires Stow
  entirely on a foreign host; or a Guix System migration declared
  out of scope and spawned as its own epic. This work-item executes
  the chosen strategy.
- `deployment-management-06` is **superseded for the user-side
  surface**. The privileged-surface relationship depends on the `/etc`
  strategy: re-scoped to the privileged surface only (thin adapter),
  retired entirely (bespoke farmer), or deferred (Guix System).
  Whichever applies, `docs/work-items/deployment-management-06-flat-packages-manifest.md`
  receives a status amendment recording the supersession.
- `guix pull` remains forbidden. The `home-configuration.scm` is
  applied via `guix time-machine -C channels.scm -- home reconfigure`
  so the staleness contract from `guix-02` covers Guix Home as well.

## Dependencies

- [Work Item guix-02](guix-02-package-adoption.md) must ship first.
  This work-item assumes `guix/channels.scm`, `guix/manifest.scm`,
  `scripts/guix-deploy.sh`, and the `ARCHIE_GUIX_*` env contract are
  already in place.
- [Work Item guix-01](guix-01-evaluation-and-poc.md) must have
  produced an `/etc` strategy recommendation. This work-item
  executes it.
- [Work Item deployment-management-06](deployment-management-06-flat-packages-manifest.md)
  is partially or fully superseded by this work-item. The exact shape
  of the supersession follows the chosen `/etc` strategy.
- [Epic guix](../epics/guix.md) defines the staged adoption shape.
- `lib/bash/lib.sh:load_repo_env_file` continues to be the env-loading
  hook for any new `ARCHIE_GUIX_*` toggles introduced here.

## Scope Notes

Included:

- Authoring `guix/home-configuration.scm` covering every file
  currently owned by the Stow `home`, `config`, `local`, and
  `p10k-*` packages. The selector group becomes a Scheme `cond` on
  `ARCHIE_P10K_PACKAGE`.
- A `scripts/guix-home-deploy.sh` thin wrapper that loads `.env.sh`
  and runs
  `guix time-machine -C "$ARCHIE_GUIX_CHANNELS_FILE" -- home reconfigure "$ARCHIE_GUIX_HOME_CONFIG_FILE"`.
- A new `deploy_guix_home` step in `scripts/install.sh` invoking the
  wrapper, gated by `ARCHIE_GUIX_HOME_ENABLED`.
- Retiring the user-side Stow packages: `home`, `config`, `local`,
  `p10k-classic`, `p10k-lean`, `p10k-pure`, `p10k-rainbow`. The
  directory contents are migrated into the Guix Home configuration
  before the package directories are removed.
- Executing the `/etc` strategy recommendation from `guix-01`:
  - **If thin Stow adapter**: keep the privileged Stow packages
    (`etc`, `sddm-theme`, `lid-close`, `nvidia`, `xkb`) and re-scope
    `deployment-management-06`'s manifest to cover only those.
    Retire the user-side `deploy_stow_packages` branches.
  - **If bespoke symlink farmer**: write the farmer in
    `lib/bash/guix-etc.sh`, package the privileged files as a Guix
    package or service that materializes a profile under
    `/gnu/store`, and have `scripts/install.sh` symlink-farm from
    that profile into `/etc`. Retire all Stow packages and
    `deployment-management-06` entirely.
  - **If Guix System migration**: declare it out of scope, retire
    the user-side Stow packages, leave the privileged Stow packages
    untouched as a transitional state, and spawn a new epic.
- Adding `ARCHIE_GUIX_HOME_ENABLED` and
  `ARCHIE_GUIX_HOME_CONFIG_FILE` (default `guix/home-configuration.scm`)
  to `.env.dist.sh`.
- Realigning `docs/user/GUIDE.md` so the Stow command lists are
  replaced by a `guix home reconfigure` reference for `$HOME` and the
  chosen mechanism for `/etc`.
- Amending the status of
  `docs/work-items/deployment-management-06-flat-packages-manifest.md`
  to record the supersession.

Not included:

- Re-evaluating the `/etc` strategy. `guix-01` decided it; this
  work-item executes it.
- Migrating to Guix System. If that is the chosen strategy, this
  work-item only declares it out of scope and spawns the epic.
- Touching `guix/manifest.scm` or `guix/channels.scm` beyond the
  additions Guix Home requires (for example, declaring Guix Home as
  a profile dependency if needed).

## Main Quests

### 1. Author `home-configuration.scm`

Translate every file currently owned by the Stow `home`, `config`,
`local`, and `p10k-*` packages into Guix Home services. Use
`home-files-service-type` for direct `$HOME` files,
`home-xdg-configuration-files-service-type` for `~/.config`, and
`home-files-service-type` rooted under `~/.local` for the `local`
package. Implement the `p10k-*` selector as a Scheme `cond` against
the value of `ARCHIE_P10K_PACKAGE`, defaulting to `p10k-lean`.

The configuration must source files from a deterministic location in
the repo so a Guix Home rebuild against an unchanged channel pin
produces a byte-identical profile.

### 2. Implement the deploy wrapper and installer integration

Write `scripts/guix-home-deploy.sh` mirroring
`scripts/guix-deploy.sh` from `guix-02`. Add `deploy_guix_home` to
`scripts/install.sh` that invokes the wrapper, gated by
`ARCHIE_GUIX_HOME_ENABLED`. The new step runs after
`deploy_guix_packages`. Add `ARCHIE_GUIX_HOME_ENABLED` and
`ARCHIE_GUIX_HOME_CONFIG_FILE` to `.env.dist.sh`.

### 3. Execute the `/etc` strategy

Branch on `guix-01`'s recommendation:

- **Thin Stow adapter**: retain the privileged Stow packages, re-scope
  `deployment-packages/manifest.yml` (the WI-06 artifact) to cover
  only `etc`, `sddm-theme`, `lid-close`, `nvidia`, and `xkb`. Update
  WI-06's status to reflect the re-scope.
- **Bespoke symlink farmer**: write `lib/bash/guix-etc.sh` and the
  privileged-file Guix package. Refactor `scripts/install.sh` to
  symlink-farm from the materialized profile. Retire all
  `deployment-packages/` content and amend WI-06 to "superseded".
- **Guix System migration**: declare out of scope, retire only the
  user-side Stow packages, leave the privileged Stow packages
  untouched, and create `docs/epics/guix-system.md` (or equivalent)
  as a follow-up.

### 4. Retire the user-side Stow packages

Remove `deployment-packages/home`, `deployment-packages/config`,
`deployment-packages/local`, `deployment-packages/p10k-classic`,
`deployment-packages/p10k-lean`, `deployment-packages/p10k-pure`, and
`deployment-packages/p10k-rainbow`. Remove the corresponding branches
from `deploy_stow_packages` in `scripts/install.sh`. Remove the
`backup_stow_conflicts` invocations that targeted those packages.

### 5. Realign documentation and verify

Update `docs/user/GUIDE.md`:

- Replace the user-side `stow --dir deployment-packages --target ...`
  blocks with a `scripts/guix-home-deploy.sh` invocation and a
  pointer to `guix/home-configuration.scm`.
- Replace or retain the `/etc` blocks per the chosen strategy.

Update `docs/user/QUICKSTART.md`, `docs/user/MIGRATING.md`, and
`docs/user/KEYBOARD_CUSTOMIZATIONS.md` for consistency with the new
contract.

Amend
`docs/work-items/deployment-management-06-flat-packages-manifest.md`'s
`## Status` and `## Decision Changes` sections to record the
supersession.

Verify by:

- Running `scripts/install.sh` end to end on a clean disposable VM
  and confirming `$HOME` and `/etc` end up byte-identical to a
  pre-supersession Stow-driven install (modulo the symlink targets,
  which now point into `/gnu/store/...`).
- Running `scripts/guix-home-deploy.sh` standalone on an
  already-deployed system and confirming idempotency: no spurious
  profile generations, no rewritten symlinks.
- Exercising rollback (`guix home roll-back`) and confirming `$HOME`
  reverts to the previous generation cleanly.
- Reproducing the same `$HOME` profile on two VMs from the same
  channel pin and `home-configuration.scm`. The resulting symlink
  trees must be structurally identical.
- Running `shellcheck` on `scripts/guix-home-deploy.sh` and the
  refactored `scripts/install.sh`.

## Acceptance Criteria

- `guix/home-configuration.scm` exists and exhaustively describes
  every file previously owned by the user-side Stow packages,
  including the `p10k-*` selector logic.
- `scripts/guix-home-deploy.sh` exists and is the documented
  entrypoint for redeploying `$HOME` configuration.
- `scripts/install.sh` invokes `deploy_guix_home` gated by
  `ARCHIE_GUIX_HOME_ENABLED` and contains no `stow_package` or
  `stow_package_sudo` calls targeting `home`, `config`, `local`, or
  any `p10k-*` package.
- `.env.dist.sh` exposes `ARCHIE_GUIX_HOME_ENABLED` and
  `ARCHIE_GUIX_HOME_CONFIG_FILE` loaded through
  `lib/bash/lib.sh:load_repo_env_file`.
- The user-side `deployment-packages/` directories
  (`home`, `config`, `local`, `p10k-*`) are removed from the repo.
- The `/etc` strategy recommended by `guix-01` is implemented as
  defined under Quest 3.
- `deployment-management-06`'s status reflects the supersession or
  re-scope.
- `docs/user/GUIDE.md`, `docs/user/QUICKSTART.md`,
  `docs/user/MIGRATING.md`, and `docs/user/KEYBOARD_CUSTOMIZATIONS.md`
  reference the Guix Home flow and contain no user-side
  `stow --dir deployment-packages --target ...` invocations beyond
  frozen historical references inside earlier work-items.

## Metadata

### id

guix-03
