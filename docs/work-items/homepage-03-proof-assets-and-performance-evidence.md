# Work Item 3: Create Proof Assets And Performance Evidence For Homepage Claims

<!--toc:start-->

- [Work Item 3: Create Proof Assets And Performance Evidence For Homepage Claims](#work-item-3-create-proof-assets-and-performance-evidence-for-homepage-claims)
  - [Status](#status)
  - [Outcome](#outcome)
  - [Decision changes](#decision-changes)
  - [Dependencies](#dependencies)
  - [Scope Notes](#scope-notes)
  - [Main quests](#main-quests)
  - [Exit Criteria](#exit-criteria)
<!--toc:end-->

Create the supporting screenshots, workload examples, and benchmark evidence
needed for stronger homepage claims about Archie’s responsiveness and overhead.

## Status

Backlog

## Outcome

Archie has a reproducible set of proof assets and measurement guidance that can
support homepage language about responsiveness, practical overhead, and
real-world multitasking behavior.

## Decision changes

- This work item exists to prevent homepage messaging from drifting into
  unverified marketing language.
- Real workload demonstrations are useful proof, but they should be paired with
  at least a small set of concrete measurements.
- Proof assets should be reproducible enough that future homepage revisions can
  refresh them without inventing a new process.

## Dependencies

- [Work Item 1](homepage-01-product-positioning-and-site-structure.md) defines
  which claims require evidence before publication.
- [Work Item 2](homepage-02-homepage-implementation.md) may consume interim
  assets, but any stronger performance messaging should wait for this work.

## Scope Notes

Included:

- Define a repeatable measurement workflow for homepage performance proof.
- Capture screenshots and workload examples representative of real Archie use.
- Document which metrics are headline-safe and how they were obtained.

Not included:

- Full benchmarking infrastructure unless lightweight automation proves
  necessary.
- Competitive performance shootouts beyond what the homepage needs.

## Main quests

- Decide the minimum benchmark set needed to support homepage messaging, such
  as:
  - idle memory footprint after login
  - CPU or memory behavior under a representative multitasking workload
  - startup-to-usable-desktop timing if practical
- Define the representative showcase workload for Archie, including realistic
  examples such as concurrent browser, terminal, editor, and agent sessions.
- Capture or refresh screenshots that demonstrate both the desktop’s visual
  identity and the chosen workload scenario.
- Document the command or workflow used to gather the measurements so later
  updates can reproduce them.
- Decide which measured results are stable enough for public homepage use and
  which should remain internal reference only.

## Exit Criteria

- Archie has a repeatable proof workflow for homepage screenshots and core
  measurements.
- Homepage-safe performance statements are explicitly backed by recorded
  evidence.
- Future homepage revisions can refresh the supporting assets without
  re-deciding the proof strategy.
