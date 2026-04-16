# Automated Documentation Maintenance

Documentation and code drift silently. A function added to a shell library goes
undocumented. A function removed or renamed leaves a stale entry in the README.
Neither failure is caught by any existing check. This work item designs and
implements a tool that closes that gap by reconciling shell library source files
with their co-located READMEs using git history to identify what changed and
what needs attention.

## Status

planned

## Outcome

Running `uv run python -m archie doc check` against a shell library and its
README produces a structured report that flags missing documentation for new
functions, alerts on README entries whose implementations no longer exist, and
suppresses false positives for intentionally deprecated symbols.

## Main Quests

### Design: detection model

The tool must answer two questions for any `(source_file, readme_file)` pair:

1. **What changed in the source?** Compare the current function list against
   the function list at the last commit that also touched the README. Any
   function present in the source but absent from the README, and introduced
   after that shared commit, is a candidate for a documentation suggestion.

2. **What is orphaned in the README?** Any function documented in the README
   but absent from the source is a validation failure — unless it appears under
   a heading whose text matches a deprecations pattern (e.g. `## Deprecations`,
   `## Deprecated`, or any heading containing the word "deprecat" case-insensitively).

The tool does not write documentation. It only reports and suggests.

#### Git history strategy

For a given source file `lib/functions.sh` and its README `lib/README.md`:

1. Find the most recent commit that touched **both** files simultaneously (the
   last time they were kept in sync).
2. Collect all functions defined in `lib/functions.sh` at that commit — this is
   the documentation baseline.
3. Diff the current function list against the baseline to identify additions and
   removals since the last sync.
4. Functions added since the last sync and absent from the README are
   undocumented — emit a suggestion.
5. Functions present in the README but absent from the current source are
   orphaned — emit a validation failure, unless they appear under a deprecations
   heading.

When no shared commit exists (the pair has never been synced), treat the entire
current source as undocumented relative to an empty baseline.

### Design: function extraction

The tool must parse bash source files to extract a canonical list of defined
functions. A function definition matches either of these two forms:

```
function_name() {
function function_name {
```

Only top-level definitions are relevant; nested or dynamically constructed
names are out of scope.

The README parser must extract documented function names. Convention: each
function is documented under a heading (any level) whose text is or contains
the function name, or as a list item or code span that names the function
explicitly. For the initial implementation, a conservative approach is
acceptable: treat any fenced code block header or `###`/`####` heading that
matches a known function name as documentation evidence.

### Design: output format

**Suggestions** (code changed, README not updated):

```
SUGGEST lib/README.md: document `new_function` (added in <commit-sha>)
```

**Validation failures** (README documents something absent from source):

```
FAIL lib/README.md: `removed_function` is documented but not defined in lib/functions.sh
```

**Clean state:**

```
OK lib/functions.sh <-> lib/README.md
```

Exit code is non-zero when any `FAIL` line is emitted. `SUGGEST` lines do not
affect exit code — they are advisory.

### Implementation: CLI entry point

The tool lives in a Python package at the repository root, invokable as:

```
uv run python -m archie doc check [path]
```

`path` defaults to the repository root. The tool discovers `(source, readme)`
pairs by walking directories and applying a pairing convention:

- Any `*.sh` file whose sibling directory contains a `README.md` forms a pair.
- The initial implementation targets `lib/` subdirectories specifically; general
  discovery can be added incrementally.

The tool must be runnable with no external dependencies beyond the Python
standard library and `git` being on `PATH`.

### Side-quests

#### Shellcheck integration point

The `doc check` command should be designed so that a future `doc lint` command
can sit alongside it and invoke `shellcheck` on the same source files. Share
the file-discovery logic between both commands from the start to avoid
duplication when `lint` is added.

#### Configuration stub

Reserve a `[tool.archie.doc]` section in `pyproject.toml` (or equivalent) for
future configuration such as custom deprecations heading patterns or explicit
pair overrides. Do not implement configuration parsing in this work item — only
ensure the section exists and is documented as a future extension point.

## Acceptance Criteria

- `uv run python -m archie doc check` runs without error on the repository root.
- Given `lib/functions.sh` with a function added after the last README update,
  the tool emits a `SUGGEST` line for that function.
- Given a README that documents a function no longer present in the source, the
  tool emits a `FAIL` line and exits non-zero.
- Given a README that documents a function under a `## Deprecations` heading
  (or any heading whose text contains "deprecat"), no `FAIL` is emitted for
  that function even if it is absent from the source.
- `SUGGEST` lines do not cause a non-zero exit on their own.
- The file-discovery logic is factored into a module that a future `doc lint`
  command can import without modification.

## Metadata

### id

infrastructure-01
