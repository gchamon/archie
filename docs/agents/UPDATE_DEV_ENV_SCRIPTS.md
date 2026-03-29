These development-environment scripts are derived from
`./docs/development/DEV_ENV.md`, which remains the canonical reference for
creating, launching, and interacting with Archie VMs.

When updating the Archie VM convenience scripts, treat these files as one unit:

- `./scripts/create-arch-base-image.sh`
- `./scripts/launch-archie-instance.sh`
- `./scripts/cleanup-archie-instance.sh`
- `./scripts/launch-console.sh`
- `./scripts/open-shell.sh`
- `./scripts/setup-shared-clipboard.sh`
- `./scripts/dev-env/common.sh`
- `./scripts/dev-env/ssh-clipboard-sync.sh`
- `./lib/bash/lib.sh`
- `./docs/development/DEV_ENV.md`
- `./CONTRIBUTING.md`

Update them in this order:

1. Re-read the relevant sections of `./docs/development/DEV_ENV.md`.
2. Update the convenience entrypoints in `./scripts/` so their defaults,
   sequencing, logging, and output still match the canonical workflow.
3. Update `./scripts/dev-env/common.sh` only for dev-env domain logic such as
   Incus defaults, state
   directories, guest IP lookup, and cloud-init or agent waiting.
4. Update `./lib/bash/lib.sh` only for generic shell helpers shared across
   scripts, such as logging, command execution, or command discovery.
5. Update `./scripts/dev-env/ssh-clipboard-sync.sh` only when
   the clipboard transport contract itself changes.
6. Update `./docs/development/DEV_ENV.md` so its prose and
   examples match the scripts exactly while preserving its role as the source
   of truth.
7. Update `./CONTRIBUTING.md` if the contributor-facing entrypoints or linked
   implementation artifacts change.

When making changes, preserve these boundaries:

- `./docs/development/DEV_ENV.md` is canonical.
- The root `./scripts/*.sh` files are convenience entrypoints over that
  documented workflow.
- `./scripts/dev-env/common.sh` contains dev-env helpers, not generic shell
  utilities.
- `./lib/bash/lib.sh` contains generic shell helpers, not Incus-specific logic.
- `./scripts/dev-env/ssh-clipboard-sync.sh` is a specialized
  clipboard bridge and should not become a second source of truth for the
  broader VM workflow.

Verify at least the following after updates:

1. `bash -n` passes for every modified script under `./scripts/`.
2. The script defaults still match the documented `ARCHIE_BASE_*` and
   `ARCHIE_INSTANCE_*` variables in
   `./docs/development/DEV_ENV.md`.
3. The base-image flow still renders the bootstrap cloud-init template from
   `./templates/dev-env/cloud-init/user-data.yaml.tpl`.
4. The launch flow still renders the Archie instance cloud-init template from
   `./templates/dev-env/cloud-init/archie-instance-user-data.yaml.tpl`
   and uses
   `./templates/dev-env/incus/archie-instance-raw-qemu.conf`.
5. Waiting for the Incus VM agent and waiting for `cloud-init` remain distinct
   phases.
6. `./scripts/open-shell.sh` still resolves the guest IP from the launched
   instance and opens an interactive SSH shell using
   `ARCHIE_INSTANCE_SSH_IDENTITY`.
7. `./scripts/setup-shared-clipboard.sh` still resolves the guest IP from the
   launched instance and delegates to
   `./scripts/dev-env/ssh-clipboard-sync.sh`.
8. `./CONTRIBUTING.md` still points contributors to the correct script
   entrypoints and supporting files.

Do not let the convenience scripts become a second source of truth. If a
script grows behavior that is no longer recoverable from
`./docs/development/DEV_ENV.md`, update the canonical
documentation in the same change.
