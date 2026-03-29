# Work Item 4: Add Derived Quickstart And Uninstall Automation

<!--toc:start-->

- [Work Item 4: Add Derived Quickstart And Uninstall Automation](#work-item-4-add-derived-quickstart-and-uninstall-automation)
  - [Status](#status)
  - [Outcome](#outcome)
  - [Decision changes](#decision-changes)
  - [Dependencies](#dependencies)
  - [Scope Notes](#scope-notes)
  - [Main quests](#main-quests)
    - [1. Define the quickstart boundary](#1-define-the-quickstart-boundary)
    - [2. Define the automation artifacts](#2-define-the-automation-artifacts)
    - [3. Define the executable interfaces](#3-define-the-executable-interfaces)
    - [4. Define the uninstall phases](#4-define-the-uninstall-phases)
    - [5. Define the derivation contract](#5-define-the-derivation-contract)
    - [6. Leave implementation intent explicit](#6-leave-implementation-intent-explicit)
    - [Side-quests](#side-quests)
  - [Exit Criteria](#exit-criteria)
<!--toc:end-->

Define and document derived helper automation around the canonical deployment
and migration guides: a fast onboarding path and a staged uninstall helper that
first restores backed-up config paths and later reverts Archie-managed package
installs.

## Status

Complete

Post-delivery notice: `scripts/quickstart.sh` was renamed to
`scripts/install.sh` after this work item was delivered. Historical references
in this document are preserved as originally delivered.

## Outcome

Archie has a short onboarding path for first-time deployment and a staged
uninstall helper plan, both clearly derived from the canonical user guides
rather than replacing them.

## Decision changes

- `docs/user/GUIDE.md` remains the canonical source of truth for deployment
  instructions.
- `docs/user/MIGRATING.md` remains the canonical source of truth for rollback
  and restore semantics until the uninstall helper is implemented and then
  documented against it.
- The quickstart is a derived artifact intended to optimize first-run setup,
  not a replacement for the full deployment guide.
- The preferred quickstart shape is script-first: a small user-facing
  `docs/user/QUICKSTART.md` should explain and point to an executable helper, while
  machine-specific edits remain explicit manual follow-up steps.
- The preferred quickstart launch path is `vet` against the GitLab raw script.
  Running `./scripts/quickstart.sh` from an existing checkout remains a
  supported repo-local entrypoint.
- The executable helper should live at `scripts/quickstart.sh` because it is a
  repo-maintained onboarding tool, not a deployed runtime script under a Stow
  package.
- The uninstall helper should live at `scripts/uninstall.sh` because it is a
  repo-maintained maintenance tool that reverses Archie deployment state rather
  than a deployed runtime script.
- Quickstart maintenance is agent-driven in this phase. The repo should define
  how an agent updates the derived quickstart and uninstall artifacts when the
  canonical guides change.
- The quickstart must automate only the common first-run path already described
  by `docs/user/GUIDE.md`: base package installation, `yay` bootstrap, the common
  Archie package set, cloning the repo, Stow deployment, scaffolding local
  files from deployed `.dist` templates, zsh package installation, and the
  required home-directory bootstrap step.
- The quickstart helper has two explicit execution modes:
  1. bootstrap mode when launched outside a checkout, where it clones Archie
     into `ARCHIE_CHECKOUT_DIR_NAME`
  2. repo mode when launched inside an existing checkout, where it uses that
     checkout directly
- The quickstart must preserve manual ownership of machine-specific values. It
  may create files from templates and stop for user edits, but it must not
  guess monitor names, backlight device identifiers, wallpaper paths, zsh
  overrides content, or similar host-specific values.
- The quickstart now includes theming setup as part of the first-run path. It
  should install the theme packages, deploy exactly one `p10k-*` package, and
  apply the documented SDDM and GTK theming steps while still keeping the full
  guide as the canonical explanation of those choices.
- The quickstart must not absorb reference material from the full guide such as
  Nvidia instructions, boot tuning, ACPI backlight tuning, lid-close hibernate,
  or service customization. Those remain guide-only topics.
- Keyring setup is part of the quickstart path and should be automated rather
  than left as guide-only follow-up.
- Quickstart configuration is repo-scoped via `.env.sh`, with documented
  defaults in `.env.dist.sh` and command-line environment variables taking
  precedence over `.env.sh`.
- The quickstart backup step is part of the helper contract, not an incidental
  implementation detail. It must move conflicting unmanaged deployment targets
  into configurable backup roots while skipping paths already managed by Stow
  symlink trees.
- The default quickstart choices are part of the documented interface:
  `p10k-lean` for the prompt, `Adwaita-dark` for GTK, `gnome-keyring` and
  `seahorse` for keyring setup, non-interactive package installs, and SDDM
  theme customization enabled by default, with opt-out through
  `ARCHIE_ENABLE_SDDM_THEME=0`.
- Archie keyboard customizations are not part of the default quickstart
  baseline. Deployment of the `xkb` package is opt-in behind
  `ARCHIE_ENABLE_XKB_CUSTOMIZATIONS=1`.
- `yay` bootstrap behavior is now explicit: prefer `yay-bin`, and if `yay` is
  present without `yay-bin`, normalize back to `yay-bin`.
- The initial uninstall helper phase is a convenience wrapper around the
  restore procedure already documented in `docs/user/MIGRATING.md`. It must
  remove Archie-managed Stow links and restore backed-up paths from the known
  backup roots without inventing different rollback semantics.
- The later uninstall helper phase must remove only Archie-managed packages
  that were not explicit packages before Archie installation. It must not
  remove unrelated packages installed by the user after the initial Archie
  setup.
- The derivation contract must be explicit: `docs/user/QUICKSTART.md`,
  `scripts/quickstart.sh`, `scripts/uninstall.sh`, and the agent maintenance
  brief are derived artifacts whose command list and sequencing must stay
  aligned with `docs/user/GUIDE.md` and `docs/user/MIGRATING.md`.
- Markdown TOC maintenance should be automated as a side-quest under this work
  item because it supports the same derived-doc workflow touched by the
  quickstart and uninstall artifacts. The automation artifact should live at
  `maint-scripts/update-markdown-toc-build.sh`.
- The quickstart should fail closed when assumptions are missing. It may prompt
  the user to edit generated local files, but it should not silently continue
  past required manual decisions.
- The quickstart execution strategy is two-phase:
  1. land a primary non-interactive script that covers the canonical quickstart
     flow end to end
  2. expand that script with guided user interaction that runs the usual
     inspection commands, presents the discovered values, and asks the user to
     choose the values to write into machine-specific configs
- The uninstall execution strategy is also staged inside this work item:
  1. land a restore-focused `scripts/uninstall.sh` that automates Stow cleanup
     and backup restoration
  2. expand it with explicit-package snapshot support so it can remove
     Archie-managed packages that were not present before installation
- This work belongs to the existing `deployment-management` epic because it is
  an extension of the deployment documentation and onboarding flow, not a new
  standalone docs or agent-workflow initiative.

## Dependencies

- [Work Item 1](deployment-management-01-design.md) defines the Stow package and
  target model that the quickstart and uninstall helpers must use.
- [Work Item 2](deployment-management-02-restructure.md) made the package layout
  and deployment commands real, including the migration rollback procedure that
  the uninstall helper initially wraps.
- [Work Item 3](deployment-management-03-documentation.md) made
  `docs/user/GUIDE.md` the current canonical deployment reference and
  documented the symlink-aware `.dist` workflow that the quickstart must
  preserve.

## Scope Notes

This work item is still primarily a planning artifact. It is intended to remove
open questions before implementation starts in later execution passes,
including the staged plan for quickstart and uninstall automation.

Included:

- Defining the exact boundary between canonical guide content and the derived
  quickstart path.
- Choosing the quickstart and uninstall artifact set and their responsibilities.
- Defining the executable helper interfaces and the steps they may automate.
- Defining the quickstart configuration contract exposed through `.env.sh`,
  `.env.dist.sh`, and command-line environment variables.
- Defining the staged execution plan that starts with a working primary
  quickstart script, then adds guided interaction for machine-specific value
  selection, and later adds uninstall package-state reversal.
- Defining the maintenance contract an agent will use to refresh the derived
  helper artifacts when the canonical guides change.
- Capturing bounded side-quests discovered during this work item when they
  materially affect the same docs or maintenance helpers.

Not included:

- Writing `docs/user/QUICKSTART.md`.
- Implementing `scripts/quickstart.sh`.
- Implementing `scripts/uninstall.sh`.
- Writing the new agent brief under `docs/agents/`.
- Adding CI or lint automation for the quickstart workflow.

## Main quests

### 1. Define the quickstart boundary

- Map the quickstart path to the canonical guide sections that represent the
  common first-run flow:
  - `1.1 Install Essential Packages`
  - `1.2 Install Yay (AUR Helper)`
  - `1.3 Install Essential Packages with Yay`
  - repo clone under `2. Deploying system config`
  - `2.1 Deploy Archie with Stow`
  - the file-creation parts of `2.2 System specific configuration`
  - `2.3 Zsh setup`
  - `2.4 Add required home folders`
  - all of `3. Theming`
  - the keyring setup portion of `4. System config customizations`
- Record the sections that remain guide-only follow-up material:
  - the non-keyring parts of `4. System config customizations`
  - any future sections whose primary purpose is reference material, hardware
    specialization, preference tuning, or optional post-install enhancement

### 2. Define the automation artifacts

- `docs/user/QUICKSTART.md` should be a short entrypoint document that:
  - states that `docs/user/GUIDE.md` is canonical
  - states that the quickstart is a derived fast path
  - tells the reader when to use the quickstart and when to drop back to the
    full guide
  - documents the preferred `vet` bootstrap path and the repo-local fallback
  - points to `scripts/quickstart.sh`
  - documents bootstrap mode and repo mode at a high level
  - documents that quickstart can be configured through `.env.sh` and the
    quickstart-specific variables in `.env.dist.sh`
  - lists the manual follow-up edits the script intentionally leaves to the
    user
- `scripts/quickstart.sh` should be the only executable in the quickstart path.
  It should:
  - run the package installation and Stow deployment commands that already
    exist in `docs/user/GUIDE.md`
  - support both bootstrap mode and repo mode without changing the deployment
    semantics
  - scaffold machine-local files from deployed `.dist` templates using the same
    symlink-aware `readlink -f` pattern documented in the guide
  - load `.env.sh` automatically when present and honor command-line
    environment overrides
  - back up conflicting unmanaged Stow targets into the configured backup
    roots while skipping already managed symlink trees
  - treat XKB deployment as optional and only back up or deploy the `xkb`
    package when the XKB quickstart toggle is enabled
  - apply the theme-install and theme-selection steps that are now part of the
    quickstart path
  - apply the documented keyring setup steps
  - stop and tell the user which generated files now require manual editing
  - leave deeper system customization to the guide
- `scripts/uninstall.sh` should be the executable in the uninstall path. It
  should:
  - start as a convenience wrapper for the restore procedure documented in
    `docs/user/MIGRATING.md`
  - remove the Archie-managed Stow links for `home`, the selected `p10k-*`
    package, `config`, `local`, `etc`, and `xkb`
  - restore backed-up user and system paths from
    `~/archie-pre-stow-backup` and `/root/archie-pre-stow-backup`
  - preserve the same symlink-aware restore semantics documented in the
    migration guide rather than inventing a different rollback flow
  - later grow package-removal support based on a pre-install package snapshot
- `docs/agents/UPDATE_QUICKSTART.md` should tell an agent how to refresh the
  derived helper artifacts from the canonical docs without letting them become
  a second source of truth

### 3. Define the executable interfaces

- The helpers should be runnable as `./scripts/quickstart.sh` and
  `./scripts/uninstall.sh`.
- The helpers should be written in Bash and follow the repo shell conventions.
- The preferred user-facing quickstart entrypoint should be `vet` against the
  raw `scripts/quickstart.sh` URL, while keeping `./scripts/quickstart.sh` as
  the supported repo-local entrypoint.
- `scripts/quickstart.sh` may group work into visible phases such as package
  bootstrap, repository clone, Stow deployment, local-file scaffolding, zsh
  setup, theming, keyring setup, and post-install reminders.
- `scripts/uninstall.sh` may group work into visible phases such as Stow
  removal, backup restoration, and later package cleanup.
- Both helpers should print the exact commands they are about to run or
  otherwise keep the flow auditable.
- The helpers should not require flags in the initial implementation unless a
  flag is needed to avoid destructive ambiguity. A single common path is
  preferred for v1.
- `scripts/quickstart.sh` should expose configuration through environment
  variables loaded from `.env.sh` with documented defaults in `.env.dist.sh`.
- `scripts/quickstart.sh` should be designed so a later iteration can add
  guided prompts around inspected machine values without rewriting the whole
  flow.
- `scripts/quickstart.sh` must never:
  - overwrite an existing machine-local file such as `device.conf`,
    `hyprpaper.conf`, or `overrides.sh` without an explicit user decision
  - infer host-specific config values
  - hide the need to review `docs/user/GUIDE.md` for optional or machine-specific
    follow-up work
  - treat already managed Stow symlink trees as backup conflicts
- `scripts/uninstall.sh` must never:
  - remove machine-specific local files that were never backed up or managed by
    Archie
  - remove packages outside the Archie-managed package set during the later
    package-removal phase
  - diverge from the restore semantics already established by
    `docs/user/MIGRATING.md` without the canonical docs being updated first

### 4. Define the uninstall phases

- Phase 1 of `scripts/uninstall.sh` should be a restore wrapper only:
  - remove Stow-managed Archie links that quickstart or manual deployment added
  - restore backed-up user and system paths from the standard backup roots or
    the configured quickstart backup roots when those were overridden
  - work for failed migration rollback and for reverting any previously
    deployed Archie config files that were moved aside into those backup roots
  - treat this as convenience automation over the migration-guide restore
    procedure, not a new uninstall model
- Phase 2 of `scripts/uninstall.sh` should extend the script with package
  reversal:
  - `scripts/quickstart.sh` must capture a pre-install inventory of explicit
    packages before installing Archie packages
  - the uninstall flow must compare that snapshot against the current explicit
    package state
  - the removal set must be the Archie-managed package set minus the packages
    already explicit before installation
  - packages installed later by the user for unrelated reasons must remain
    untouched even if they are not in the snapshot
- Quickstart interactive customization remains part of this work item, but it
  should be treated as a later quickstart-specific pass after the primary
  quickstart script is stable.

### 5. Define the derivation contract

- The canonical source for quickstart command content is `docs/user/GUIDE.md`.
- The canonical source for uninstall restore behavior is
  `docs/user/MIGRATING.md`.
- The quickstart implementation must stay aligned with the actual user-facing
  launch and configuration contract documented in `docs/user/QUICKSTART.md`
  and `.env.dist.sh`, not just the command flow in `docs/user/GUIDE.md`.
- The implementation session should keep a clearly labeled mapping between
  guide sections and helper-script phases so future updates can be traced.
- `docs/user/QUICKSTART.md` should summarize and link; it should not restate the full
  rationale or duplicate long command explanations from the guide.
- `scripts/quickstart.sh` should embed only the command flow needed to execute
  the fast path. When the guide changes, the script must be reviewed against the
  same guide sections rather than independently evolved.
- `scripts/uninstall.sh` should embed only the command flow needed to reverse
  Archie deployment state. When the migration guide changes, the script must be
  reviewed against the same rollback procedure rather than independently
  evolved.
- The agent brief should instruct the agent to update the quickstart in this
  order:
  1. Re-read the relevant sections of `docs/user/GUIDE.md`.
  2. Update `scripts/quickstart.sh` to match the canonical commands and file
     scaffolding behavior.
  3. Re-read `docs/user/QUICKSTART.md` and `.env.dist.sh` so the launch modes,
     defaults, and quickstart environment contract stay aligned with the
     script.
  4. Re-read the relevant rollback sections of `docs/user/MIGRATING.md`.
  5. Update `scripts/uninstall.sh` so its Stow cleanup and restore behavior
     matches the canonical rollback procedure.
  6. Update `docs/user/QUICKSTART.md` and any future uninstall-facing doc so
     their prose matches the scripts and preserves the canonical-versus-derived
     framing.
  7. Verify that the interactive prompts still derive their inspection commands
     and write targets from the guide-backed flow rather than ad hoc logic.
  8. Verify that any intentionally excluded topics still remain excluded.

### 6. Leave implementation intent explicit

- The later execution sessions should implement the derived helpers in stages
  rather than all at once.
- The implementation should happen in this order:
  1. build and validate the primary script-first quickstart flow
  2. build and validate the restore-focused `scripts/uninstall.sh` flow
  3. extend `scripts/quickstart.sh` with guided interaction for machine-specific
     value discovery and selection
  4. extend `scripts/quickstart.sh` and `scripts/uninstall.sh` with the package
     inventory contract and Archie-managed package removal
- The implementation sessions should validate each helper with shell linting
  and a dry run or audited execution where possible, then re-check the
  user-facing prose against the final script behavior before closing the work
  item.

### Side-quests

- Add Markdown TOC upkeep automation as a bounded side-quest attached to this
  work item's documentation-maintenance surface area.
- Implement that automation in `maint-scripts/update-markdown-toc-build.sh`.
  Its contract should be:
  - process tracked `*.md` files from git
  - skip files marked with `<!--toc:ignore-->`
  - insert or update managed `<!--toc:start-->` / `<!--toc:end-->` blocks
  - use `toc-markdown`, installing it via `uv` when needed
- Keep this side-quest secondary to the main quickstart and uninstall
  automation outcomes. It should improve maintenance of derived docs and work
  items without redefining the primary outcome of this work item.

## Exit Criteria

- A reader can identify `docs/user/GUIDE.md` as the canonical deployment reference
  and `docs/user/QUICKSTART.md` as the fast path.
- A reader can identify `docs/user/MIGRATING.md` as the canonical rollback
  reference and understand that `scripts/uninstall.sh` derives from it.
- The quickstart path covers the common first-run deployment flow, including
  theming and keyring setup, without guessing machine-specific configuration
  choices.
- The uninstall path is defined in two explicit phases: restore automation
  first, package reversal second.
- The later package-reversal phase is constrained to Archie-managed packages
  absent from a pre-install explicit-package snapshot.
- The repo contains explicit agent-facing instructions for updating the derived
  helper artifacts when the canonical guides change.
- The work item makes the staged plan for later quickstart interaction and
  uninstall package reversal explicit enough that the implementation sessions
  can add them without reopening scope.
- The work item leaves implementation intent clear enough that later execution
  sessions can add the helper artifacts without reopening scope or ownership
  decisions.
- The work item explicitly defines the Markdown TOC automation side-quest and
  its implementation contract.
