# Contributing

<!--toc:start-->

- [Contributing](#contributing)
  - [AI-Assisted Contributions](#ai-assisted-contributions)
  - [Development Environment](#development-environment)
  - [Maintainer Tools](#maintainer-tools)
  - [Project Maintenance](#project-maintenance)
<!--toc:end-->

This repository contains both Archie itself and the documentation used to
maintain it. This file is the contributor-facing entrypoint for maintenance and
development workflows.

## AI-Assisted Contributions

AI-assisted contributions are welcome.

If a contribution was prepared with meaningful AI assistance, disclose that
clearly during merge request review. The specific AI provider does not need to
be named unless the contributor believes that detail is genuinely necessary for
review.

Review should focus on the quality of the contribution itself. Provider
disclosure is intentionally not required by default in order to avoid reviewer
bias toward or against a particular AI tool.

## Development Environment

For the Archie development guest workflow, start with
[docs/development/DEV_ENV.md](docs/development/DEV_ENV.md).

The main terminal entrypoints are:

- [scripts/create-arch-base-image.sh](scripts/create-arch-base-image.sh)
- [scripts/launch-archie-instance.sh](scripts/launch-archie-instance.sh)
- [scripts/cleanup-archie-instance.sh](scripts/cleanup-archie-instance.sh)
- [scripts/launch-console.sh](scripts/launch-console.sh)
- [scripts/setup-shared-clipboard.sh](scripts/setup-shared-clipboard.sh)

That workflow also depends on these repo-owned artifacts:

- [scripts/dev-env/ssh-clipboard-sync.sh](scripts/dev-env/ssh-clipboard-sync.sh)
- [scripts/dev-env/common.sh](scripts/dev-env/common.sh)
- [templates/dev-env/cloud-init/user-data.yaml.tpl](templates/dev-env/cloud-init/user-data.yaml.tpl)
- [templates/dev-env/cloud-init/archie-instance-user-data.yaml.tpl](templates/dev-env/cloud-init/archie-instance-user-data.yaml.tpl)
- [templates/dev-env/incus/archie-instance-raw-qemu.conf](templates/dev-env/incus/archie-instance-raw-qemu.conf)

The host-side tooling baseline used by that flow is documented in
[docs/user/DEVELOPMENT.md](docs/user/DEVELOPMENT.md).

Repo-wide Bash helper functions live under `lib/bash/`. Executable entrypoints
remain under `scripts/` and `maint-scripts/`.

## Maintainer Tools

Repo maintenance helpers under [maint-scripts](maint-scripts/README.md) use
`uv`-managed CLIs where practical.

Current maintainer tooling:

- `toc-markdown` for Markdown TOC generation

Install the tool:

```bash
uv tool install toc-markdown
```

Inspect installed `uv` tools:

```bash
uv tool list
```

Upgrade one tool:

```bash
uv tool upgrade toc-markdown
```

Upgrade all `uv`-managed tools:

```bash
uv tool upgrade --all
```

## Project Maintenance

Repo-internal planning and design material lives under:

- [docs/work-items/README.md](docs/work-items/README.md)
- [docs/architecture/decisions/README.md](docs/architecture/decisions/README.md)
- [docs/README.md](docs/README.md)
