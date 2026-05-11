# Guix

## Status

Planned

## Outcome

Archie should have a decision-backed Guix track that determines whether
GNU Guix can serve as Archie's deployment substrate — covering
user-space package management and `$HOME` configuration deployment —
under a configurable staleness contract that pins channel commits to a
floor of at least N days old (default 7) via `guix time-machine`. The
track is staged: an evaluation and proof-of-concept work-item gates a
package-only adoption work-item, which in turn gates a Guix Home
adoption work-item that supersedes the user-side surface of
`deployment-management-06`.

## Work items

- [guix-01-evaluation-and-poc](/docs/work-items/guix-01-evaluation-and-poc.md)
- [guix-02-package-adoption](/docs/work-items/guix-02-package-adoption.md)
- [guix-03-home-adoption-and-stow-supersession](/docs/work-items/guix-03-home-adoption-and-stow-supersession.md)

## Decision Changes

- `guix` is the canonical epic name for Archie work that evaluates and
  adopts GNU Guix as a deployment substrate. It is distinct from the
  `immutability` epic, which evaluates image-style base-system
  management through `arkdep`. arkdep manages the base image; Guix
  manages user-space packages and `$HOME` configuration. The two are
  layered, not competing.
- Adoption is staged. `guix-01` produces an evaluation and a
  disposable-VM proof of concept. `guix-02` adopts Guix for packages
  only, leaving Stow in place. `guix-03` adopts Guix Home for `$HOME`
  configuration and resolves the relationship with
  `deployment-management-06`. Each stage gates the next.
- Staleness is enforced exclusively through `guix time-machine` against
  a commit-pinned `channels.scm`. `guix pull` is forbidden in Archie's
  documented flow so the staleness contract stays honest.
- The Arch Linux Archive delayed-update fallback named in
  `docs/epics/immutability.md` is subsumed by this epic if Guix is
  adopted. The two solve the same reproducibility problem;
  `time-machine` is the stronger primitive.
- AUR coverage is partitioned three ways: packages already in upstream
  Guix move directly; niche desktop packages get hand-written Guix
  package definitions committed to the repo; binary blobs and `-git`
  HEAD-tracking packages either get bespoke binary package definitions
  or stay on yay as a documented residual surface.
- `/etc` deployment is resolved within `guix-03`. On an Arch-foreign
  Guix install `guix home` cannot manage `/etc`; the candidate
  resolutions are a thin Stow `/etc` adapter, a bespoke profile-based
  symlink farmer, or migration to Guix System. The choice is made in
  `guix-03`, not assumed in this epic.

## Main Quests

- Evaluate Guix as a package manager and as a configuration deployment
  substrate against Archie's current Stow + pacman + yay model.
- Run a disposable-VM proof of concept exercising packages, Guix Home,
  rollback, and the staleness floor before committing to either
  adoption stage.
- Stage the adoption so package management and configuration
  deployment migrate independently and each migration can be reverted
  without unwinding the other.

## Acceptance Criteria

- The epic explains why Guix is a distinct planning track for Archie
  and how it relates to `immutability`'s arkdep evaluation.
- The epic states that `guix-01` evaluation is the first milestone
  instead of assuming adoption.
- The epic exposes a stable `id` and explicit `child_ids`.
- The epic names the `/etc`-on-foreign-Guix problem as a deferred
  decision resolved by `guix-03`, not by this epic.

## Metadata

### id

guix

### child_ids

- guix-01
- guix-02
- guix-03

### priority

high
