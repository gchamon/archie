# Quickstart

<!--toc:start-->

- [Quickstart](#quickstart)
  - [Run It](#run-it)
  - [What It Does](#what-it-does)
  - [Defaults And Limits](#defaults-and-limits)
  - [Continue In The Full Guide](#continue-in-the-full-guide)
<!--toc:end-->

This is the fastest Archie onboarding path. It is derived from
[`docs/user/GUIDE.md`](./GUIDE.md), but [`docs/user/GUIDE.md`](./GUIDE.md) remains the
canonical deployment reference.

Use this when you want the common first-run setup with the repo-managed helper.
Drop back to the full guide when you need migration details, Nvidia-specific
setup, boot tuning, service customization, or any other machine-specific
follow-up not covered here.

## Run It

The preferred bootstrap path is to use
[`vet`](https://github.com/vet-run/vet) against the GitLab raw script instead
of piping a remote script straight into a shell.

If `vet` is not installed yet, install it first using the upstream
installation instructions or the Arch `vet` package workflow from the project
README:
<https://github.com/vet-run/vet>

If you already have `vet` installed, run:

```bash
vet https://gitlab.com/gabriel.chamon/archie/-/raw/main/scripts/quickstart.sh
```

When started this way, the script clones Archie into `~/archie` by default and
continues from there. Override that path with `ARCHIE_CHECKOUT_DIR_NAME` if you
want a different checkout location.

If you already have a local Archie checkout, you can also run the helper from
the checkout root:

```bash
cd archie
./scripts/quickstart.sh
```

Quickstart-specific environment variables are documented in
[`../../.env.dist.sh`](../../.env.dist.sh). Copy it to `.env.sh` in the repo
root, edit the values you want, and quickstart will load that file
automatically. For example, to opt into the SDDM theme path while debugging:

```bash
cp ./.env.dist.sh ./.env.sh
${EDITOR:-vi} ./.env.sh
./scripts/quickstart.sh
```

If you also pass quickstart environment variables on the command line, those
command-line values take precedence over `.env.sh`:

```bash
ARCHIE_ENABLE_SDDM_THEME=0 ./scripts/quickstart.sh
```

For example, to opt into Archie keyboard customizations as part of quickstart:

```bash
ARCHIE_ENABLE_XKB_CUSTOMIZATIONS=1 ./scripts/quickstart.sh
```

The script behaves in two modes:

- bootstrap mode: when run outside a checkout, it clones `archie` first
- repo mode: when run from an existing checkout, it uses that checkout directly

## What It Does

The helper runs the common first-run path from the canonical guide:

- installs the base packages and bootstraps `yay`
- clones Archie when the script was launched from the GitLab raw URL
- backs up pre-existing deployment targets that would conflict with Archie
  Stow packages into `~/archie-pre-stow-backup` and
  `/root/archie-pre-stow-backup`
  while skipping paths already managed by Stow symlink trees
- installs the common Archie package set
- deploys the Stow packages into `~`, `~/.config`, `~/.local`, `/etc`, and
  optionally `/usr/share/xkeyboard-config-2`
- scaffolds `device.conf`, `hyprpaper.conf`, and `overrides.sh` from the
  deployed `.dist` templates if they do not already exist
- installs the zsh, theming, and keyring packages
- deploys `p10k-lean` as the default Powerlevel10k theme
- optionally installs and configures the SDDM `slice` theme
- applies a best-effort GTK theme setup for `Adwaita-dark`
- creates `~/Pictures/Screenshots`
- prints the manual follow-up commands needed to finish machine-specific
  configuration

## Defaults And Limits

The quickstart intentionally makes a few fixed choices:

- the default prompt theme is `p10k-lean`
- the default GTK theme target is `Adwaita-dark`
- keyring setup installs `gnome-keyring` and `seahorse`
- `yay` is bootstrapped from `yay-bin` only when `yay-bin` is missing
- if `yay` is installed but `yay-bin` is missing, quickstart normalizes the system back to `yay-bin`
- SDDM theme customization is enabled by default; set `ARCHIE_ENABLE_SDDM_THEME=0` to disable it
- keyboard customizations are disabled by default; set `ARCHIE_ENABLE_XKB_CUSTOMIZATIONS=1` to deploy the `xkb` package
- package installs run non-interactively
- `yay` review menus default to `N`
- `yay` removes make dependencies after successful installs

The helper does not guess machine-specific values on its own. If discovery
commands are unavailable or incomplete, it leaves the generated local files in
place and tells you what to edit manually.

## Continue In The Full Guide

After the quickstart completes, use [`docs/user/GUIDE.md`](./GUIDE.md) for:

- migration from older Archie deployments
- Nvidia setup
- boot and backlight tuning
- lid-close power behavior
- service customization
- any manual review of `device.conf`, `hyprpaper.conf`, or `overrides.sh`
