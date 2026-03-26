# Work Item 4: Add A Derived Quickstart And Maintenance Workflow

Define and document a fast deployment path derived from the main deployment
guide, plus the maintenance workflow that keeps it aligned with the canonical
instructions.

## Status

Planned

## Outcome

Archie has a short onboarding path for first-time deployment that is clearly
derived from `docs/GUIDE.md`, while the full guide remains the canonical
reference for explanations, optional setup, and machine-specific decisions.

## Decision changes

- `docs/GUIDE.md` remains the canonical source of truth for deployment
  instructions.
- The quickstart is a derived artifact intended to optimize first-run setup,
  not a replacement for the full deployment guide.
- The preferred quickstart shape is script-first: a small user-facing
  `docs/QUICKSTART.md` should explain and point to an executable helper, while
  machine-specific edits remain explicit manual follow-up steps.
- Quickstart maintenance is agent-driven in this phase. The repo should define
  how an agent updates the derived quickstart artifacts when the canonical guide
  changes.
- This work belongs to the existing `deployment-management` epic because it is
  an extension of the deployment documentation and onboarding flow, not a new
  standalone docs or agent-workflow initiative.

## Tasks

- Define which parts of `docs/GUIDE.md` are in scope for the derived
  quickstart, including package installation, repo cloning, Stow deployment,
  local file scaffolding from deployed `.dist` templates, zsh setup, and
  immediate post-install steps.
- Define which guide sections must stay out of the quickstart path, such as
  theming, Nvidia-specific instructions, boot tuning, power-management
  customization, and other machine- or preference-specific reference material.
- Design the quickstart executable interface, including what it automates, what
  it scaffolds, and which machine-specific values it must never guess.
- Add a concise `docs/QUICKSTART.md` that explains the quickstart path, its
  limits, and where to continue in the full guide.
- Add a repo-local agent brief under `docs/agents/` that tells an agent how to
  update the quickstart artifacts from `docs/GUIDE.md` and preserve the
  canonical-versus-derived boundary.
- Document or encode the derivation contract so the quickstart artifacts can be
  maintained without duplicating deployment logic in multiple places.

## Exit Criteria

- A reader can identify `docs/GUIDE.md` as the canonical deployment reference
  and `docs/QUICKSTART.md` as the fast path.
- The quickstart path covers the common first-run deployment flow without
  attempting to automate machine-specific configuration choices.
- The repo contains explicit agent-facing instructions for updating the derived
  quickstart artifacts when the guide changes.
- The work item leaves implementation intent clear enough that a later execution
  session can add the quickstart artifacts without reopening the scope or
  ownership decisions.
