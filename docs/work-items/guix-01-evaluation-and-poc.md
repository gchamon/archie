# Evaluate Guix As Archie's Deployment Substrate And Run A Disposable-VM Proof Of Concept

Position GNU Guix as a deployment-substrate candidate for Archie that
covers user-space packages *and* `$HOME` configuration, gated by a
configurable staleness floor (`ARCHIE_GUIX_STALENESS_DAYS`, default
`7`) implemented via `guix time-machine`. Produce the partition
decisions and the proof-of-concept evidence that `guix-02` and
`guix-03` need before committing to adoption.

## Status

Planned

## Outcome

The Guix track has a decision-backed go/no-go recommendation grounded
in concrete VM evidence. The work-item produces: Archie-specific
evaluation criteria; a three-way partition of every entry in
`ESSENTIAL_PACKAGES`, `ZSH_PACKAGES`, `THEME_PACKAGES`, and
`KEYRING_PACKAGES` (`scripts/install.sh` lines 11-81) into
upstream-Guix / locally-defined-recipe / residual-yay; a partition of
`deployment-packages/` into Guix-Home-replaceable / `/etc`-residual; a
disposable-VM proof of concept exercising packages, Guix Home,
rollback, and the staleness floor; and an explicit recommendation
that either green-lights `guix-02` and `guix-03` or kills the track.

## Decision Changes

- This work-item produces evaluation evidence only. It does not modify
  `scripts/install.sh`, `.env.dist.sh`, `docs/user/GUIDE.md`, or
  `deployment-packages/`. Production changes land in `guix-02` and
  `guix-03`.
- The Arch Linux Archive delayed-update fallback named in the
  `immutability` epic is in scope for direct comparison. The
  recommendation must argue whether `guix time-machine` subsumes it.
- The recommendation must take a position on the AUR partition (which
  niche packages are worth maintaining as local Guix recipes versus
  staying on yay) and on the `/etc` strategy (thin Stow adapter,
  bespoke symlink farmer, or Guix System migration). Those positions
  become the input contract for `guix-02` and `guix-03`.
- `guix pull` is forbidden in Archie's documented flow. The staleness
  contract is enforced exclusively through `guix time-machine` against
  a pinned `channels.scm`.

## Dependencies

- [Epic guix](../epics/guix.md) defines the staged adoption shape this
  work-item gates.
- [Work Item immutability-01](immutability-01-arkdep-evaluation-and-poc.md)
  is the parallel evaluation. This work-item must contrast Guix
  against arkdep explicitly and argue arkdep and Guix are layered
  (base image vs user-space) rather than competing.
- [Work Item deployment-management-06](deployment-management-06-flat-packages-manifest.md)
  defines the manifest-as-contract pattern this evaluation must compare
  against. The recommendation states whether `guix-03` supersedes
  WI-06, re-scopes it to `/etc`, or coexists with it.
- The `vm-image` epic provides the disposable-VM substrate the proof
  of concept runs against.

## Scope Notes

Included:

- Archie-specific evaluation criteria for Guix on a foreign Arch host.
- A three-way partition of every current pacman/yay package into
  upstream-Guix / locally-defined-recipe / residual-yay.
- A two-way partition of every `deployment-packages/` package into
  Guix-Home-replaceable / `/etc`-residual.
- A disposable-VM proof of concept that exercises:
  - `guix time-machine -C channels.scm -- package -m manifest.scm`
    against a representative manifest covering a CLI tool, a TUI
    app, a Wayland-aware GUI app, a font, and a zsh plugin.
  - `guix home reconfigure` against a representative
    `home-configuration.scm` covering at least the `home`, `config`,
    `local`, and one `p10k-*` package's worth of files.
  - Profile rollback (`guix package --roll-back`,
    `guix home roll-back`).
  - Channel-pin staleness floor: a `channels.scm` with commits pinned
    to ≥ 7 days old, refreshed by a throwaway script, and verified to
    install the expected versions.
- A written recipe-maintenance assessment for at least three niche
  desktop packages (Hyprland, `sddm-slice-qt6-git`, `grimblast-git`):
  how hard is each to package, who maintains the upstream, what is
  the ongoing churn cost.
- A written `/etc` strategy recommendation with a stated cost for each
  candidate (thin Stow adapter, bespoke symlink farmer, Guix System
  migration).
- A go/no-go recommendation that names downstream work-items.

Not included:

- Any production change to `scripts/install.sh`, `.env.dist.sh`,
  `docs/user/GUIDE.md`, or `deployment-packages/`.
- Adopting Guix System. If the `/etc` recommendation is "migrate to
  Guix System", that becomes a follow-up epic, not part of this
  work-item.
- Authoring the production `guix/manifest.scm`, `guix/channels.scm`,
  or `home-configuration.scm`. Throwaway POC versions only.
- Touching `docs/epics/immutability.md` to record the ALA subsumption
  decision. That amendment is mechanical follow-up.

## Main Quests

### 1. Define evaluation criteria and the partitions

Document Archie-specific evaluation criteria so the proof of concept
in Quest 2 produces a defensible recommendation. Criteria must include:
bootstrap independence (Guix cannot install itself before pacman has
run), profile and `PATH` integration with zsh, locale and glibc interop
between Guix profiles and Arch system libraries, GUI application
behavior under per-user Guix profiles, rollback granularity compared
to arkdep's image-level rollback, the operational cost of refreshing
pinned channel commits, and the recipe-maintenance burden for the AUR
desktop niche.

In the same quest produce two partitions:

- Every entry in `ESSENTIAL_PACKAGES`, `ZSH_PACKAGES`,
  `THEME_PACKAGES`, and `KEYRING_PACKAGES` is classified as
  upstream-Guix, locally-defined-recipe, or residual-yay. Document
  the classification rule and the per-package result.
- Every package directory under `deployment-packages/` is classified
  as Guix-Home-replaceable or `/etc`-residual. Document the rule and
  the per-package result.

Surface the overlap with the Arch Linux Archive delayed-update fallback
named in `docs/epics/immutability.md` and argue whether
`time-machine` subsumes it.

### 2. Disposable-VM proof of concept

Reuse the disposable-VM discipline established by `immutability-01`.
From the reproducible base image produced by the `vm-image` epic,
install Guix on an Arch host, then exercise:

- A representative package manifest pinned to a channel commit ≥ 7
  days old, installed via `guix time-machine -C channels.scm --
  package -m manifest.scm`. Validate that the installed versions
  match the pin.
- A representative Guix Home configuration covering files currently
  owned by the Stow `home`, `config`, `local`, and a single `p10k-*`
  package. Validate that `guix home reconfigure` produces the
  expected symlink farm and that `$PATH`, `$XDG_DATA_DIRS`, and zsh
  init source the Guix profile correctly.
- Rollback for both layers (`guix package --roll-back`,
  `guix home roll-back`). Confirm rollback is profile-generation
  granular and does not require touching the channel pin.
- A throwaway channel-pin refresh tool that walks each channel's
  upstream git history, picks the newest commit older than 7 days,
  and rewrites `channels.scm`. Validate idempotency on a pin that
  already satisfies the threshold.

Capture friction notes inline under this quest.

### 3. Recipe-maintenance assessment

Pick three packages from the locally-defined-recipe partition produced
in Quest 1 — at minimum `hyprland`, `sddm-slice-qt6-git`, and
`grimblast-git` — and write throwaway Guix package definitions for
them. Record: time to first working build, upstream churn rate
(commits per month), runtime dependency depth, and any patches
required. Use the result to estimate ongoing recipe-maintenance cost
in operator-hours per month.

### 4. `/etc` strategy assessment

Document each candidate resolution to the `/etc`-on-foreign-Guix
problem with a stated cost:

- Thin Stow `/etc` adapter: smallest change, keeps `deployment-management-06`
  partially relevant, requires Archie to maintain two deployment
  systems forever.
- Bespoke symlink farmer over a Guix-built profile: medium change,
  retires Stow entirely on a foreign host, custom code Archie owns.
- Guix System migration: largest change, retires both Stow and Arch,
  out of scope for `guix-02`/`guix-03` and would spawn its own epic.

Recommend one. The recommendation becomes the input contract for
`guix-03`.

### 5. Recommendation and downstream work-item shape

Produce a written recommendation: proceed with `guix-02` and `guix-03`
as defined; proceed with `guix-02` only and defer `guix-03`; or kill
the Guix track. If proceed, name any new work-items the recommendation
creates beyond `guix-02` and `guix-03` (for example, a `guix-04`
recipe-maintenance pipeline if Quest 3 reveals enough churn to
warrant one).

## Acceptance Criteria

- Evaluation criteria are Archie-specific and explicitly contrast Guix
  against arkdep and against the Arch Linux Archive fallback.
- The three-way package partition and two-way `deployment-packages/`
  partition are complete: every current entry has a classification
  and a one-line rationale.
- The disposable-VM proof of concept ran end to end and produced
  concrete friction notes captured in this work-item.
- At least three locally-defined Guix recipes were written and built
  successfully in the POC, and a recipe-maintenance cost estimate
  exists.
- The `/etc` strategy recommendation names a single chosen approach
  and states the cost of the rejected approaches.
- The work-item ends with an explicit proceed / partial-proceed /
  reject recommendation that names every downstream work-item it
  creates.

## Implementation Notes

### Preparation status

POC preparation is staged for manual VM execution. Throwaway assets live
under ignored path `.state/guix-01-poc/`:

- `README.md`: manual runbook for the disposable VM.
- `channels.scm`: single-channel Guix pin draft, refreshed by the
  throwaway helper before use.
- `manifest.scm`: representative package manifest covering a CLI tool,
  TUI app, Wayland-session GUI app, font, and zsh plugin.
- `home-configuration.scm`: representative Guix Home config covering
  files from the `home`, `config`, `local`, and `p10k-lean` Stow
  surfaces.
- `packages/archie-poc.scm`: throwaway recipe drafts for `grimblast`,
  `sddm-slice-qt6`, and a Hyprland inheritance probe.
- `scripts/refresh-channels.sh`: staleness-floor channel pin refresher.
- `scripts/collect-evidence.sh`: read-only snapshot helper for manual
  evidence capture.
- `evidence-template.md`: manual results template to copy back from the
  VM.

These assets are not production `guix-02`/`guix-03` artifacts. They are
only the POC kit.

### Evaluation criteria

- **Bootstrap independence**: Guix is allowed to enter only after the
  Arch bootstrap can install enough tooling to fetch, install, and
  operate Guix. It must not become a prerequisite for installing itself.
- **Zsh/profile integration**: Guix profile activation must work for
  interactive zsh sessions without relying on ad hoc manual exports.
  `$PATH`, `$GUIX_PROFILE`, and `$XDG_DATA_DIRS` must be observable in
  the VM evidence.
- **Arch/Guix runtime interop**: CLI, TUI, GUI, font, and zsh-plugin
  examples must run from the per-user Guix profile on an Arch host
  without locale, glibc, icon-theme, portal, or dynamic-linker
  breakage.
- **GUI behavior**: a Wayland-session GUI package must launch from the
  Guix profile against the Arch compositor/session services already in
  the VM baseline.
- **Rollback granularity**: Guix package and home rollbacks must be
  generation-granular and user-space scoped. arkdep rollback remains
  image/base-system scoped, so the two mechanisms are layered rather
  than competing.
- **Staleness operation cost**: `guix time-machine` against
  `channels.scm` must enforce a configurable floor, defaulting to
  `ARCHIE_GUIX_STALENESS_DAYS=7`, without `guix pull`.
- **AUR recipe cost**: packages that are absent from upstream Guix must
  be evaluated for build complexity, upstream churn, runtime dependency
  depth, and operator-hours per month.
- **ALA fallback comparison**: if `guix time-machine` provides pinned,
  reproducible user-space package state with lower operational burden
  than Arch Linux Archive delayed updates, the recommendation should
  treat ALA as superseded for the Guix-managed package surface. ALA may
  remain relevant for residual pacman/yay packages.

### Package partition

Classification rule:

- **upstream-Guix**: use upstream Guix when the package exists at the
  selected channel pin with acceptable functional equivalence.
- **locally-defined-recipe**: write and maintain an Archie recipe when
  upstream Guix is absent or unsuitable and the package is central to
  Archie.
- **residual-yay**: keep on pacman/yay when the package is bootstrap,
  hardware/system-bound, binary-only, Arch-specific, HEAD-tracking, or
  too expensive to maintain as a Guix recipe.

Initial partition to verify during the POC:

| Source array | Package | Classification | Rationale |
| --- | --- | --- | --- |
| `ESSENTIAL_PACKAGES` | `acpi` | upstream-Guix | Small CLI utility; expected upstream equivalent. |
| `ESSENTIAL_PACKAGES` | `bc` | upstream-Guix | Core calculator utility; standard Guix package. |
| `ESSENTIAL_PACKAGES` | `bind` | upstream-Guix | DNS tooling maps to Guix BIND package. |
| `ESSENTIAL_PACKAGES` | `blueman` | upstream-Guix | User-space Bluetooth GUI; verify Arch D-Bus/service interop. |
| `ESSENTIAL_PACKAGES` | `brightnessctl` | upstream-Guix | CLI utility; verify device permissions remain Arch-managed. |
| `ESSENTIAL_PACKAGES` | `calibre` | upstream-Guix | Large GUI app; good cross-runtime validation target. |
| `ESSENTIAL_PACKAGES` | `cliphist` | locally-defined-recipe | Wayland clipboard helper may need local recipe if absent upstream. |
| `ESSENTIAL_PACKAGES` | `dunst` | upstream-Guix | Notification daemon; verify service/session integration. |
| `ESSENTIAL_PACKAGES` | `fd` | upstream-Guix | CLI search tool; standard Guix package may be named `fd`. |
| `ESSENTIAL_PACKAGES` | `frece` | locally-defined-recipe | Niche CLI helper; likely absent or low-priority upstream. |
| `ESSENTIAL_PACKAGES` | `fzf` | upstream-Guix | Standard CLI/TUI tool. |
| `ESSENTIAL_PACKAGES` | `gnome-system-monitor` | upstream-Guix | GUI app; verify desktop integration. |
| `ESSENTIAL_PACKAGES` | `grimblast-git` | locally-defined-recipe | Hyprland-specific helper and required recipe-assessment target. |
| `ESSENTIAL_PACKAGES` | `htop` | upstream-Guix | Standard TUI package. |
| `ESSENTIAL_PACKAGES` | `hyprcursor` | upstream-Guix | Hyprland ecosystem library; verify channel availability. |
| `ESSENTIAL_PACKAGES` | `hyprlock` | upstream-Guix | Hyprland ecosystem app; verify PAM/session assumptions. |
| `ESSENTIAL_PACKAGES` | `hyprpaper` | upstream-Guix | Hyprland ecosystem app; verify runtime session behavior. |
| `ESSENTIAL_PACKAGES` | `inotify-tools` | upstream-Guix | Standard CLI utility. |
| `ESSENTIAL_PACKAGES` | `jq` | upstream-Guix | Standard CLI utility. |
| `ESSENTIAL_PACKAGES` | `kdeconnect` | upstream-Guix | GUI/service package; verify Arch service/session interop. |
| `ESSENTIAL_PACKAGES` | `ksnip` | upstream-Guix | Screenshot GUI; verify availability and portal behavior. |
| `ESSENTIAL_PACKAGES` | `less` | upstream-Guix | Standard pager. |
| `ESSENTIAL_PACKAGES` | `lsd` | upstream-Guix | CLI replacement; verify upstream package name. |
| `ESSENTIAL_PACKAGES` | `man-db` | upstream-Guix | Documentation tooling; verify profile manpath behavior. |
| `ESSENTIAL_PACKAGES` | `ncdu` | upstream-Guix | Standard TUI package. |
| `ESSENTIAL_PACKAGES` | `noto-fonts` | upstream-Guix | Maps to Guix Noto font packages; verify exact split. |
| `ESSENTIAL_PACKAGES` | `noto-fonts-emoji` | upstream-Guix | Maps to Guix Noto emoji font package. |
| `ESSENTIAL_PACKAGES` | `otf-font-awesome` | upstream-Guix | Font package; verify exact Guix name. |
| `ESSENTIAL_PACKAGES` | `pamixer` | upstream-Guix | PulseAudio/PipeWire CLI; verify runtime audio stack interop. |
| `ESSENTIAL_PACKAGES` | `pavucontrol` | upstream-Guix | GUI app; representative Wayland-session GUI target. |
| `ESSENTIAL_PACKAGES` | `polkit-kde-agent` | residual-yay | Session/system authentication agent is safer left Arch-managed unless POC proves clean Guix ownership. |
| `ESSENTIAL_PACKAGES` | `plocate` | upstream-Guix | CLI database tool; system index timer remains Arch-owned. |
| `ESSENTIAL_PACKAGES` | `ranger` | upstream-Guix | TUI file manager. |
| `ESSENTIAL_PACKAGES` | `ripgrep` | upstream-Guix | Representative CLI target. |
| `ESSENTIAL_PACKAGES` | `rofi-wayland` | upstream-Guix | Wayland launcher; verify exact Guix package and display behavior. |
| `ESSENTIAL_PACKAGES` | `rsync` | upstream-Guix | Standard CLI utility. |
| `ESSENTIAL_PACKAGES` | `stow` | residual-yay | Deployment bootstrap tool remains Arch-side until Guix Home supersedes Stow. |
| `ESSENTIAL_PACKAGES` | `unzip` | upstream-Guix | Standard archive utility. |
| `ESSENTIAL_PACKAGES` | `waybar` | upstream-Guix | Wayland bar; verify module/runtime dependency coverage. |
| `ESSENTIAL_PACKAGES` | `wl-clip-persist` | locally-defined-recipe | Niche Wayland clipboard helper likely needs local recipe. |
| `ESSENTIAL_PACKAGES` | `xorg-xhost` | upstream-Guix | X11 compatibility utility; verify exact package name. |
| `ESSENTIAL_PACKAGES` | `zen-browser-bin` | residual-yay | Binary browser package; keep residual unless a maintained Guix source exists. |
| `ESSENTIAL_PACKAGES` | `zip` | upstream-Guix | Standard archive utility. |
| `ESSENTIAL_PACKAGES` | `zsh-fast-syntax-highlighting` | upstream-Guix | Representative zsh plugin target; verify exact Guix name. |
| `ZSH_PACKAGES` | `zsh` | upstream-Guix | Shell package; profile integration must be tested carefully. |
| `ZSH_PACKAGES` | `zsh-completions` | upstream-Guix | Shell plugin package. |
| `ZSH_PACKAGES` | `oh-my-zsh-git` | locally-defined-recipe | AUR Git package; package pinned source or replace with Guix equivalent. |
| `ZSH_PACKAGES` | `zsh-theme-powerlevel10k` | upstream-Guix | Theme package; verify exact Guix name and font interaction. |
| `ZSH_PACKAGES` | `ttf-meslo-nerd` | upstream-Guix | Nerd font package; verify Guix font split/name. |
| `THEME_PACKAGES` | `archlinux-wallpaper` | residual-yay | Arch-specific artwork; no strong reason to move to Guix. |
| `THEME_PACKAGES` | `gnome-themes-extra` | upstream-Guix | GTK theme package. |
| `THEME_PACKAGES` | `qt5ct` | upstream-Guix | Qt configuration app; verify Arch/Guix plugin path behavior. |
| `THEME_PACKAGES` | `qt5-graphicaleffects` | upstream-Guix | Qt runtime dependency; verify exact package name. |
| `THEME_PACKAGES` | `qt6ct` | upstream-Guix | Qt configuration app; verify Arch/Guix plugin path behavior. |
| `THEME_PACKAGES` | `xcursor-breeze5` | upstream-Guix | Cursor theme; verify exact Guix naming. |
| `THEME_PACKAGES` | `xdg-desktop-portal-gnome` | residual-yay | Portal service should stay aligned with Arch session packages. |
| `THEME_PACKAGES` | `xdg-desktop-portal-gtk` | residual-yay | Portal service should stay aligned with Arch session packages. |
| `THEME_PACKAGES` | `nwg-look` | upstream-Guix | GTK settings GUI; verify upstream availability. |
| `KEYRING_PACKAGES` | `gnome-keyring` | residual-yay | Login/session secret service should remain Arch-owned unless POC proves clean handoff. |
| `KEYRING_PACKAGES` | `seahorse` | upstream-Guix | User GUI for keyring inspection can be Guix-managed. |
| SDDM theme install step | `sddm-slice-qt6-git` | locally-defined-recipe | Required recipe-assessment target and SDDM theme asset. |

### Deployment-package partition

Classification rule:

- **Guix-Home-replaceable**: files target `$HOME`, `$HOME/.config`,
  `$HOME/.local`, or the selected Powerlevel10k profile and can be
  expressed with Guix Home file services.
- **`/etc`-residual**: files require privileged system target roots or
  live outside Guix Home's foreign-host ownership boundary.

| Package directory | Classification | Rationale |
| --- | --- | --- |
| `config` | Guix-Home-replaceable | Owns XDG config under `$HOME/.config`. |
| `etc` | `/etc`-residual | Owns system files under `/etc`. |
| `home` | Guix-Home-replaceable | Owns direct home files such as `.zshrc`. |
| `lid-close` | `/etc`-residual | Owns systemd/logind policy under `/etc`. |
| `local` | Guix-Home-replaceable | Owns user-local shell library under `$HOME/.local`. |
| `nvidia` | `/etc`-residual | Owns privileged modprobe/DKMS configuration. |
| `p10k-classic` | Guix-Home-replaceable | Powerlevel10k selector variant for `$HOME/.p10k.zsh`. |
| `p10k-lean` | Guix-Home-replaceable | Default Powerlevel10k selector variant. |
| `p10k-pure` | Guix-Home-replaceable | Powerlevel10k selector variant. |
| `p10k-rainbow` | Guix-Home-replaceable | Powerlevel10k selector variant. |
| `sddm-theme` | `/etc`-residual | Owns SDDM system configuration under `/etc`. |
| `xkb` | `/etc`-residual | Owns keyboard files under `/usr/share/xkeyboard-config-2`. |

### Manual POC runbook

Use the local Incus image alias `archie/reproducible-baseline`.

1. Launch a disposable VM:

   ```bash
   ARCHIE_INSTANCE_NAME=archie-guix-01 ./scripts/launch-archie-instance.sh
   ```

2. Copy the POC kit into the VM:

   ```bash
   incus file push -r .state/guix-01-poc archie-guix-01/home/archie/guix-01-poc
   incus exec archie-guix-01 -- chown -R archie:archie /home/archie/guix-01-poc
   ```

3. In the VM, install Guix through the Arch host path being evaluated.
   Record exact commands and daemon/substitute-key steps in
   `.state/guix-01-poc/evidence-template.md`.

4. Refresh and verify channel pinning:

   ```bash
   cd ~/guix-01-poc
   ./scripts/refresh-channels.sh
   ./scripts/refresh-channels.sh --check
   ```

5. Install representative packages:

   ```bash
   guix time-machine -C channels.scm -- package -m manifest.scm
   ./scripts/collect-evidence.sh package-after-install
   ```

6. Reconfigure Guix Home:

   ```bash
   ARCHIE_REPO_ROOT="$HOME/archie" \
     guix time-machine -C channels.scm -- home reconfigure home-configuration.scm
   ./scripts/collect-evidence.sh home-after-reconfigure
   ```

7. Exercise rollback:

   ```bash
   guix package --roll-back
   ./scripts/collect-evidence.sh package-after-rollback
   guix home roll-back
   ./scripts/collect-evidence.sh home-after-rollback
   ```

8. Build recipe drafts:

   ```bash
   guix time-machine -C channels.scm -- build -L packages hyprland-poc
   guix time-machine -C channels.scm -- build -L packages grimblast
   guix time-machine -C channels.scm -- build -L packages sddm-slice-qt6
   ```

9. Capture friction notes and bring the filled evidence template back
   from the VM.

### Recipe-maintenance evidence template

For `hyprland`, `sddm-slice-qt6-git`, and `grimblast-git`, record:

- build result and time to first working build
- upstream commit rate per month for the last three months
- runtime dependency depth
- patches or substitutions required
- estimated operator-hours per month

### `/etc` strategy evidence template

Evaluate each strategy after the VM results are known:

- **Thin Stow adapter**: cost to keep only privileged
  `deployment-packages/` on Stow while Guix Home owns user files.
- **Bespoke symlink farmer**: cost to retire Stow by symlink-farming
  privileged files from a Guix-built profile.
- **Guix System migration**: cost and scope of replacing the foreign
  Arch host instead of solving `/etc` on top of it.

Record one chosen strategy before `guix-03` starts.

### ADR candidates

No ADR is accepted by this preparation pass alone. Candidate decisions
after VM evidence:

- Adopt or reject Guix as the user-space deployment substrate.
- Treat `guix time-machine` as superseding the Arch Linux Archive
  delayed-update fallback for Guix-managed packages.
- Choose the `/etc` strategy for foreign-Guix hosts.

## Metadata

### id

guix-01
