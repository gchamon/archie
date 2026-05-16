# Arch Linux Archive Downgrade CLI MVP

Archie needs a small repository-owned CLI for system maintenance tasks that are
specific to this installation. The first command should remove the manual work
from downgrading related Arch Linux packages together by resolving the right
Arch Linux Archive URLs for a requested point in time.

## Status

done

## Outcome

Running `uv run archie downgrade --to 7d linux-lts linux-lts-headers` prints a
complete `pacman -U ...` command using the newest Arch Linux Archive package
URLs at or before the requested target time. The output is suitable for piping
to a script and running separately with elevated privileges.

## Decision Changes

- Architecture support is fixed to a module-level `x86_64` constant for the
  MVP. Do not expose `--arch` until Archie needs a second architecture and the
  matching behavior can be designed around that requirement.
- Archive index parsing must support the live Arch Linux Archive timestamp
  format, such as `08-May-2026 07:23`, without depending on process locale.
- Downgrade execution is opt-in through `--execute`. The dry default remains
  the script-friendly `pacman -U ...` output, while execution uses the local
  `pacman -U` CLI and prefixes `sudo` when Archie is not already running as
  root.

## Main Quests

### Establish the Archie Python CLI

Create the real Archie Python package under `src/archie` and add project
metadata so the CLI is invokable through both console-script and module forms:

```bash
uv run archie downgrade --help
uv run python -m archie downgrade --help
```

The MVP should use only the Python standard library at runtime. Use `argparse`
for command dispatch and keep the package layout ready for future commands such
as `archie doc check`. Development dependencies may include `pytest` and
`pyright` for test execution and type validation.

### Resolve archive package matches

Implement `archie downgrade` with this interface:

```bash
uv run archie downgrade [--to TARGET] [--archive-url URL] [--execute] [--noconfirm] PACKAGE...
```

`TARGET` defaults to the current time and accepts absolute dates like
`2026-01-01` and single-unit relative values like `7d` or `4h`. For each
package, fetch the package directory from
`https://archive.archlinux.org/packages/<first-letter>/<package>/`, ignore
`.sig` files and non-matching architectures, and select the newest matching
package archive whose archive timestamp is at or before the target.

### Generate safe install output

On success, print exactly one `pacman -U <url...>` command to stdout. Do not add
`sudo` and do not execute `pacman`; the command only prepares a script line for
the user to inspect and run separately.

If any requested package cannot be resolved, emit diagnostics to stderr, exit
non-zero, and print no partial `pacman -U` command.

When `--execute` is passed, resolve all package URLs first, then run
`pacman -U <url...>` directly if already root or `sudo pacman -U <url...>` when
not root. Let pacman inherit the terminal so its prompts and progress remain
normal. `--noconfirm` passes pacman's `--noconfirm` flag in both dry output and
execution modes.

### Cover the MVP with focused tests

Add unit tests that mock archive HTML and network access. The tests should not
depend on live Arch Linux Archive availability.

## Acceptance Criteria

- `uv run archie downgrade --help` runs successfully.
- `uv run python -m archie downgrade --help` runs successfully.
- `--to` accepts `YYYY-MM-DD`, `7d`, and `4h`.
- Successful resolution prints exactly one `pacman -U` command to stdout.
- `--execute` runs the resolved `pacman -U` transaction only after all packages
  resolve successfully.
- `--noconfirm` is passed through to pacman in both dry and execute modes.
- Missing package resolution exits non-zero and prints no partial install
  command or pacman execution.
- Tests cover target parsing, archive index parsing, package filename matching,
  successful output, and fail-all behavior.
- The MVP does not introduce runtime dependencies beyond the Python standard
  library, but may use `pytest` and `pyright` as development dependencies.

## Metadata

### id

infrastructure-02
