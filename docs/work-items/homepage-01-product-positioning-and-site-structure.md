# Define Homepage Product Positioning And Site Structure

Define how Archie should be presented on a homepage as a product, including the
core message, proof strategy, target audience, and the structure of the first
landing page.

## Status

<!--
Use a short prose status for the current state of the work item.
Supported values are `backlog`, `planned`, `doing`, `done`, `cancelled`, and `abandoned`.
`killed` is reserved for GitLab graveyard history when a managed work item is removed from the repository.
-->

Planned

## Outcome

Archie has a decision-complete homepage brief that explains what the site is
trying to communicate, who it is for, what evidence supports its main claims,
and which sections the first homepage must include.

## Decision Changes

- This work item starts the `homepage` epic.
- The homepage should present Archie as a productized desktop experience, not
  only as a dotfiles repository or setup guide.
- The initial positioning should favor claims such as `lean`, `snappy`,
  `responsive`, and `daily-use ready` unless stronger performance language is
  backed by reproducible measurements.
- The page should be grounded in Archie’s actual stack and workflows, including
  Hyprland, Arch Linux, Waybar, Kitty, Zen Browser, and repo-backed deployment.
- The first version should optimize for clarity of value proposition and trust
  before broader storytelling, blogging, or secondary pages.

## Scope Notes

Included:

- Define the primary audience for the homepage.
- Define the headline positioning and supporting proof points.
- Decide the minimum section architecture for the homepage.
- Decide which screenshots, metrics, and workflow examples are needed to
  support the message.
- Decide which claims require evidence before publication.

Not included:

- Final implementation of the homepage.
- Full brand system or logo redesign unless needed to unblock homepage design.
- Broader documentation restructuring outside what the homepage links to.

## Main Quests

- Define the primary user segments the homepage should address, including which
  visitors are first priority:
  - users looking for a polished Hyprland desktop
  - users evaluating Archie as a daily-driver environment
  - contributors or technically curious readers comparing it to generic
    dotfiles repos
- Decide the homepage’s core value proposition and the language Archie should
  avoid unless benchmark data exists.
- Define the minimum homepage sections, including at least:
  - hero section
  - concise product description
  - feature or capability overview
  - workflow or usage proof
  - screenshots or visual showcase
  - install or getting-started call to action
  - links to deeper technical documentation
- Identify the strongest current proof assets already in the repository and the
  missing assets that must be created, such as:
  - fresh screenshots
  - benchmark data
  - workload showcase examples
  - deployment or setup evidence
- Decide how the homepage should relate to the current README and whether the
  README remains handbook-first while the homepage becomes marketing-first.
- Define acceptance criteria for messaging accuracy so the page does not
  overstate performance, simplicity, or hardware support.

## Acceptance Criteria

- Archie has a clear homepage brief with a defined audience, message, and site
  structure.
- The work item identifies which claims are safe now and which require
  supporting evidence first.
- An implementation-stage work item can build the homepage without reopening
  product-positioning decisions.

## Metadata

### id

homepage-01
