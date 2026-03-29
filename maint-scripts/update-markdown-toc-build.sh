#!/bin/bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  update-markdown-toc-build.sh

Update table-of-contents blocks in tracked Markdown files using toc-markdown.

Requirements:
  uv tool install toc-markdown

Behavior:
  - processes tracked *.md files from git
  - skips files containing <!--toc:ignore-->
  - skips files with fewer than two Markdown headings
  - inserts <!--toc:start--> / <!--toc:end--> after the first heading when missing
  - removes managed TOC blocks from files with fewer than two Markdown headings
  - updates managed TOC blocks in place via toc-markdown
EOF
}

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/bash/lib.sh
source "$SCRIPT_DIR/../lib/bash/lib.sh"
load_repo_env_file "$REPO_ROOT/.env.sh" 'ARCHIE_*'

START_MARKER="${ARCHIE_TOC_START_MARKER:-<!--toc:start-->}"
END_MARKER="${ARCHIE_TOC_END_MARKER:-<!--toc:end-->}"
IGNORE_MARKER="${ARCHIE_TOC_IGNORE_MARKER:-<!--toc:ignore-->}"
HEADER_PLACEHOLDER="${ARCHIE_TOC_HEADER_PLACEHOLDER:-<!--toc:header-->}"
HEADING_PATTERN='^#{1,6}[[:space:]]+[^[:space:]]'

ensure_toc_markdown() {
    if command -v toc-markdown >/dev/null 2>&1; then
        return 0
    fi

    require_command "uv"
    log_info "toc-markdown not found; installing it with uv"
    run_cmd uv tool install toc-markdown
    hash -r

    if ! command -v toc-markdown >/dev/null 2>&1; then
        log_error "toc-markdown is still unavailable after uv tool install"
        exit 1
    fi
}

insert_toc_markers() {
    local file_path="$1"
    local temp_file=""

    temp_file="$(mktemp)"

    awk \
        -v start_marker="$START_MARKER" \
        -v end_marker="$END_MARKER" '
        BEGIN {
            inserted = 0
            skip_next_blank = 0
        }

        {
            if (skip_next_blank && $0 == "") {
                skip_next_blank = 0
                next
            }
            skip_next_blank = 0

            print

            if (!inserted && $0 ~ /^#{1,6}[[:space:]]+[^[:space:]]/) {
                print ""
                print start_marker
                print end_marker
                print ""
                inserted = 1
                skip_next_blank = 1
            }
        }
        ' "$file_path" >"$temp_file"

    mv "$temp_file" "$file_path"
}

strip_toc_header_placeholder() {
    local file_path="$1"
    local temp_file=""

    temp_file="$(mktemp)"

    awk -v header_placeholder="$HEADER_PLACEHOLDER" '
        $0 == header_placeholder { next }
        { print }
    ' "$file_path" >"$temp_file"

    mv "$temp_file" "$file_path"
}

count_markdown_headings() {
    local file_path="$1"

    grep -Ec "$HEADING_PATTERN" "$file_path" || true
}

remove_toc_block() {
    local file_path="$1"
    local temp_file=""

    temp_file="$(mktemp)"

    awk \
        -v start_marker="$START_MARKER" \
        -v end_marker="$END_MARKER" '
        BEGIN {
            in_toc = 0
            skip_next_blank = 0
        }

        {
            if ($0 == start_marker) {
                in_toc = 1
                next
            }

            if (in_toc && $0 == end_marker) {
                in_toc = 0
                skip_next_blank = 1
                next
            }

            if (in_toc) {
                next
            }

            if (skip_next_blank && $0 == "") {
                skip_next_blank = 0
                next
            }

            skip_next_blank = 0
            print
        }
        ' "$file_path" >"$temp_file"

    mv "$temp_file" "$file_path"
}

handle_help_and_no_args usage "$@"

require_command "awk"
require_command "git"
require_command "grep"
require_command "mktemp"
require_command "sha256sum"
ensure_toc_markdown

processed_count=0
updated_count=0
unchanged_count=0
skipped_count=0

while IFS= read -r markdown_file; do
    ((processed_count += 1))

    if grep -qF "$IGNORE_MARKER" "$markdown_file"; then
        log_info "Skipping $markdown_file because it is marked with $IGNORE_MARKER"
        ((skipped_count += 1))
        continue
    fi

    start_count="$(grep -cF "$START_MARKER" "$markdown_file" || true)"
    end_count="$(grep -cF "$END_MARKER" "$markdown_file" || true)"

    if [[ "$start_count" != "$end_count" ]]; then
        log_error "Unbalanced TOC markers in $markdown_file"
        exit 1
    fi

    if ((start_count > 1)); then
        log_error "Multiple TOC blocks found in $markdown_file"
        exit 1
    fi

    heading_count="$(count_markdown_headings "$markdown_file")"

    if ((heading_count < 2)); then
        if ((start_count == 1)); then
            log_info "Removing TOC from $markdown_file because it has fewer than two Markdown headings"
            remove_toc_block "$markdown_file"
            ((updated_count += 1))
        else
            log_info "Skipping $markdown_file because it has fewer than two Markdown headings"
            ((skipped_count += 1))
        fi
        continue
    fi

    if ((start_count == 0)); then
        log_info "Inserting TOC markers into $markdown_file"
        insert_toc_markers "$markdown_file"
    fi

    before_hash="$(sha256sum "$markdown_file" | awk '{print $1}')"
    run_cmd toc-markdown "$markdown_file"
    strip_toc_header_placeholder "$markdown_file"
    after_hash="$(sha256sum "$markdown_file" | awk '{print $1}')"

    if [[ "$before_hash" == "$after_hash" ]]; then
        ((unchanged_count += 1))
    else
        ((updated_count += 1))
    fi
done < <(git ls-files '*.md')

printf '\nProcessed: %s\n' "$processed_count"
printf 'Updated: %s\n' "$updated_count"
printf 'Unchanged: %s\n' "$unchanged_count"
printf 'Skipped: %s\n' "$skipped_count"
