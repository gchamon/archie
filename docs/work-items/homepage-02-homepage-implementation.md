# Implement The First Archie Homepage

Implement the first Archie homepage using the approved product positioning and
site structure from the earlier planning stage.

## Status

<!--
Use a short prose status for the current state of the work item.
Supported values are `backlog`, `planned`, `doing`, `done`, `cancelled`, and `abandoned`.
`killed` is reserved for GitLab graveyard history when a managed work item is removed from the repository.
-->

Backlog

## Outcome

Archie has a polished first homepage that presents the project as a coherent
product, routes users toward installation and deeper documentation, and uses
visual and textual proof that matches the actual system.

## Decision Changes

- This work item is implementation-first and should follow the positioning
  decisions from Work Item 1 instead of redefining them.
- The first homepage should feel product-grade rather than like generated
  placeholder marketing.
- Visual design should highlight Archie’s personality and desktop identity
  while staying faithful to the system users will actually get.
- Calls to action should privilege repo-backed onboarding paths already
  documented in Archie.

## Dependencies

- [Work Item 1](homepage-01-product-positioning-and-site-structure.md) defines
  the homepage message, proof boundaries, and information architecture.

## Scope Notes

Included:

- Implement the homepage content and layout.
- Integrate approved screenshots, metrics, and calls to action.
- Link the page to the canonical README and user documentation where needed.
- Ensure the homepage works well on desktop and mobile widths.

Not included:

- Secondary marketing pages unless required by the homepage flow.
- A broader documentation site redesign.
- Automated telemetry, analytics, or marketing automation unless later work
  explicitly adds them.

## Main Quests

- Implement the homepage structure defined in Work Item 1.
- Translate the approved positioning into concise product-facing copy that
  remains technically defensible.
- Integrate visual assets that show real Archie usage rather than mockups
  detached from the repo.
- Add or refine proof sections for performance and daily usability using only
  approved evidence.
- Ensure the install and learn-more paths route users to the correct canonical
  docs, such as quickstart and the full deployment guide.
- Verify the page’s responsive behavior, readability, and visual hierarchy
  across representative desktop and mobile sizes.

## Acceptance Criteria

- Archie has a working first homepage with production-ready messaging and
  visuals.
- The page gives a product-level introduction without conflicting with the
  canonical technical documentation.
- The implemented claims, screenshots, and calls to action match Archie’s
  real capabilities and supported workflows.

## Metadata

### id

homepage-02
