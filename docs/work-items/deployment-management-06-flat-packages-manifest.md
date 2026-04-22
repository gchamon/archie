# Adopt A Manifest-Driven Flat Package Layout

Replace the current hardcoded coupling between Stow package names and their
target roots with a manifest-driven deployment contract, so Archie's
`deployment-packages/` surface can grow by data alone.

## Status

<!--
Use a short prose status for the current state of the work item.
Supported values are `backlog`, `planned`, `doing`, `done`, `cancelled`, and `abandoned`.
`killed` is reserved for GitLab graveyard history when a managed work item is removed from the repository.
-->

Planned

## Outcome

Archie's deployment surface is fully driven by a manifest at
`deployment-packages/manifest.yml`. Adding, removing, or retargeting a flat
package is a pure data change: no installer, documentation, or
agent-instruction edits are required beyond updating the manifest.

## Decision Changes

- The package-root layout established in
  [Work Item 2](deployment-management-02-restructure.md) becomes a
  manifest-described surface. Package directory names are no longer
  semantically coupled to their target roots; the coupling lives in
  `deployment-packages/manifest.yml`.
- Hardcoded `stow_package`/`stow_package_sudo` invocations and per-toggle
  branches in `scripts/install.sh` are replaced by a generic loop over
  manifest entries.
- The `xkb`, `sddm-theme`, `lid-close`, and `nvidia` opt-in semantics — and
  the `p10k-*` selector group — become declarative manifest fields, not
  installer special cases.
- `docs/user/GUIDE.md`, `docs/user/QUICKSTART.md`, `docs/user/MIGRATING.md`,
  `docs/user/KEYBOARD_CUSTOMIZATIONS.md`, and `AGENTS.md` stop listing
  per-package `stow --dir deployment-packages --target ... <package>`
  commands. They reference the manifest and a single deploy entrypoint
  instead.
- The uninstall helper planned in
  [Work Item 5](deployment-management-05-uninstall-automation.md) consumes
  the same manifest as its source of truth for which symlink trees to remove
  and which backup roots to restore from, so install and uninstall stay
  symmetrical by construction.

## Dependencies

- [Work Item 1](deployment-management-01-design.md) defines the Stow
  deployment model this manifest extends.
- [Work Item 2](deployment-management-02-restructure.md) made the current
  flat package layout concrete; this work item reshapes how that layout is
  described and executed without changing the deployed runtime paths.
- [Work Item 3](deployment-management-03-documentation.md) made the user
  guides canonical; this work item realigns them with the manifest-driven
  deploy entrypoint.
- [Work Item 4](deployment-management-04-quickstart-automation.md) shipped
  `scripts/install.sh`; this work item refactors its stow layer to consume
  the manifest.
- [Work Item 5](deployment-management-05-uninstall-automation.md) must be
  coordinated so the manifest contract covers its uninstall and restore
  needs before either ships.

## Scope Notes

Included:

- Define the manifest format, field set, and repo location.
- Define the manifest-driven deploy, backup, and uninstall contract.
- Define the migration from the current hardcoded installer to the manifest
  loop without changing user-visible deployment semantics.
- Define the documentation and agent-instruction updates required to keep
  `AGENTS.md` and the user docs aligned with the new contract.

Not included:

- Splitting any current package into multiple bundles. The initial cutover
  preserves the existing package boundaries.
- A second, per-package manifest layer. The initial design uses a single
  repo-level manifest.
- New runtime behavior in the deployed configs. This work only changes how
  deployment is described and executed, not what ends up on disk.

## Main Quests

### 1. Define the manifest format

- The manifest lives at `deployment-packages/manifest.yml`.
- YAML is parsed with `yq`, which aligns with the project's existing
  reliance on `jq` for JSON and keeps parsing outside hand-written Bash.
- The schema:
  - `version`: string. Start at `"1.0"`.
  - `deployments`: list of entries, each with:
    - `from`: package directory name relative to `deployment-packages/`.
    - `to`: target root. `$HOME` and `~` must expand against the invoking
      user's home.
    - `privileged`: boolean, default `false`. When `true`, the installer
      runs `sudo stow` for this entry.
    - `toggle`: optional name of an `ARCHIE_ENABLE_*` environment variable
      that gates the deployment.
    - `toggle_default`: optional boolean. Used when `toggle` is set and the
      environment variable is unset.
    - `selector_group`: optional string. Entries sharing a group are
      mutually exclusive at deploy time. The active member is chosen by the
      environment variable named in `selector_var`, defaulting to
      `selector_default` when unset.
    - `selector_var`: optional string. Required when `selector_group` is
      set.
    - `selector_default`: optional string. Required when `selector_group`
      is set. Exactly one entry per group carries the default.
- `yq` must be added to `ESSENTIAL_PACKAGES` in `scripts/install.sh` so the
  manifest can be parsed before `deploy_stow_packages` runs.

### 2. Author the initial manifest

Translate every current package, toggle, and p10k variant into a manifest
entry that reproduces today's behavior exactly:

- `home` → `$HOME`, unprivileged.
- `config` → `$HOME/.config`, unprivileged.
- `local` → `$HOME/.local`, unprivileged.
- `etc` → `/etc`, privileged.
- `xkb` → `/usr/share/xkeyboard-config-2`, privileged,
  `toggle: ARCHIE_ENABLE_XKB_CUSTOMIZATIONS`, `toggle_default: false`.
- `sddm-theme` → `/etc`, privileged, `toggle: ARCHIE_ENABLE_SDDM_THEME`,
  `toggle_default: true`.
- `lid-close` → `/etc`, privileged, `toggle: ARCHIE_ENABLE_LID_CLOSE`,
  `toggle_default: true`.
- `nvidia` → `/etc`, privileged, `toggle: ARCHIE_ENABLE_NVIDIA`,
  `toggle_default: false`.
- `p10k-classic`, `p10k-lean`, `p10k-pure`, `p10k-rainbow` → `$HOME`,
  `selector_group: p10k`, `selector_var: ARCHIE_P10K_PACKAGE`, with
  `selector_default: p10k-lean` carried on the `p10k-lean` entry.

### 3. Implement the manifest loader and deploy entrypoint

- Add `lib/bash/manifest.sh` with helpers that:
  - Parse `deployment-packages/manifest.yml` into iterable entries.
  - Expand `$HOME` and `~` in `to` against the invoking user.
  - Resolve toggles and selectors against the loaded `.env.sh` values and
    any command-line environment overrides.
  - Yield `(package, target, privileged)` tuples for the active deployment
    set.
- Refactor `scripts/install.sh`:
  - Replace `deploy_stow_packages` and the per-toggle branches with a loop
    over the manifest.
  - Replace `backup_existing_stow_targets` with a loop that calls the
    existing `backup_stow_conflicts`/`backup_stow_conflicts_sudo` helpers
    based on each manifest entry's `privileged` field.
  - Preserve `deploy_p10k_default` semantics by selecting the active
    selector-group entry through the manifest instead of a dedicated code
    path.
- Add `scripts/deploy.sh`: a thin wrapper that loads `.env.sh`, reads the
  manifest, and runs the same deploy loop without performing package
  installation. This becomes the canonical entrypoint for users who want
  only to (re)deploy, replacing the per-package `stow` command lists in
  the user docs.

#### Side-quests

- Add `scripts/undeploy.sh` (or a `--delete` mode on `scripts/deploy.sh`)
  so [Work Item 5](deployment-management-05-uninstall-automation.md) can
  wrap a stable, manifest-driven symlink-removal entrypoint instead of
  reimplementing manifest iteration.

### 4. Realign documentation and agent instructions

- `docs/user/GUIDE.md`: replace the per-package `stow` command lists in
  section 2.1 and the optional `/etc` block with a `scripts/deploy.sh`
  invocation plus a reference to `deployment-packages/manifest.yml`.
- `docs/user/QUICKSTART.md`: confirm it points at `scripts/install.sh`,
  which now drives deployment from the manifest. No manual `stow` commands
  should remain in the quickstart.
- `docs/user/MIGRATING.md`: rewrite the manual stow command lists in the
  rollback flow to call the manifest-driven helpers, and rebase the
  rehearsal package iteration on the manifest rather than hardcoded names.
- `docs/user/KEYBOARD_CUSTOMIZATIONS.md`: remove the bare `sudo stow`
  commands and reference the deploy helper invoked with the XKB toggle
  enabled.
- `AGENTS.md`: replace the five hardcoded
  `stow --dir deployment-packages --target ...` examples in the
  Configuration Deployment & Verification section with the manifest-aware
  helper invocation, and update Maintenance Workflow step 4 so it tells
  agents to update the manifest — not the installer — when adding
  packages.

### 5. Verification

- Bash shell `set -e` self-check: source `lib/bash/manifest.sh` and dump
  the resolved deploy plan against a fixture `.env.sh`. Confirm every
  command previously issued by `scripts/install.sh` reappears with
  identical arguments and privilege.
- Run `scripts/install.sh` end to end on a clean target (or a VM produced
  by the `dev-env` epic) to confirm no behavioral regression.
- Run `scripts/deploy.sh` standalone on an already-deployed system to
  confirm idempotency: no spurious backups, no double-symlink errors.
- Run `shellcheck` on `lib/bash/manifest.sh`, `scripts/deploy.sh`, and the
  refactored `scripts/install.sh`.

## Acceptance Criteria

- `deployment-packages/manifest.yml` exists and exhaustively describes
  every currently deployed package, including privilege, toggle, and
  selector semantics.
- `scripts/install.sh` no longer references any package name in a
  `stow_package*` call. It loops over the manifest exclusively.
- Adding a new flat package under `deployment-packages/` and registering
  it in `manifest.yml` makes it deployable without editing any other
  file.
- `scripts/deploy.sh` exists and is the documented entrypoint for
  redeploying without running the full install flow.
- No user-facing documentation or `AGENTS.md` block lists per-package
  `stow --dir deployment-packages --target ... <package>` invocations,
  other than historical references inside
  [Work Item 2](deployment-management-02-restructure.md) and
  [Work Item 3](deployment-management-03-documentation.md), which are
  frozen planning history.
- `yq` is installed early enough in `scripts/install.sh` to parse the
  manifest before `deploy_stow_packages` runs.

## Metadata

### id

deployment-management-06
