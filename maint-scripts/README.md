# Maintenance Scripts

This directory contains repo-maintenance helpers that are intended to be run by
contributors from the repository root.

## Tooling

Maintenance CLIs are managed with `uv`.

Install the current tool set:

```bash
uv tool install toc-markdown
```

Inspect installed `uv` tools:

```bash
uv tool list
```

Upgrade one maintainer tool:

```bash
uv tool upgrade toc-markdown
```

Upgrade all `uv`-managed maintainer tools:

```bash
uv tool upgrade --all
```

## Markdown TOC

`update-markdown-toc-build.sh` updates Markdown table-of-contents blocks across
tracked repo docs using `toc-markdown`.

It:

- processes tracked `*.md` files from `git ls-files`
- skips files that contain `<!--toc:ignore-->`
- inserts `<!--toc:start-->` / `<!--toc:end-->` after the first Markdown heading
  when a file has headings but no managed TOC block yet
- updates the TOC in place using the repo config in `./.toc-markdown.toml`

Run it from the repo root:

```bash
./maint-scripts/update-markdown-toc-build.sh
```
