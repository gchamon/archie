These quickstart artifacts are derived from `./docs/user/GUIDE.md`, which remains
the canonical deployment reference.

When updating the quickstart, treat these files as one unit:

- `./scripts/install.sh`
- `./docs/user/QUICKSTART.md`

Update them in this order:

1. Re-read the relevant sections of `./docs/user/GUIDE.md`.
2. Update `./scripts/install.sh` so its commands, sequencing, and local-file
   scaffolding still match the canonical guide.
3. Update `./docs/user/QUICKSTART.md` so its prose matches the script exactly while
   preserving the canonical-versus-derived framing.
4. Verify that the bootstrap path still uses `vet` against the GitLab raw
   script and that the script can clone Archie when it starts outside a local
   checkout.
5. Verify that guided prompts still use guide-backed inspection commands such
   as `hyprctl` and `brightnessctl`, and that they only write the intended
   machine-local config values.
6. Verify that non-quickstart topics remain excluded from the fast path.

Do not let the quickstart become a second source of truth. If you add
automation behavior that is no longer recoverable from `./docs/user/GUIDE.md`,
update `./docs/user/GUIDE.md` in the same change.
