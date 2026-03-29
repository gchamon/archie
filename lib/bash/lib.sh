#!/bin/bash
set -euo pipefail

LIB_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$LIB_DIR/../.." && pwd)"

matches_env_pattern() {
    local var_name="$1"
    shift
    local pattern=""

    for pattern in "$@"; do
        if [[ "$var_name" == $pattern ]]; then
            return 0
        fi
    done

    return 1
}

load_repo_env_file() {
    local env_file="${1:-$REPO_ROOT/.env.sh}"
    shift || true
    local -a patterns=("$@")
    local var_name=""
    local saved_name=""
    local -a preexisting_vars=()

    if [[ "${#patterns[@]}" -eq 0 ]]; then
        patterns=("ARCHIE_*")
    fi

    if [[ ! -f "$env_file" ]]; then
        return 0
    fi

    while IFS= read -r var_name; do
        if ! matches_env_pattern "$var_name" "${patterns[@]}"; then
            continue
        fi

        preexisting_vars+=("$var_name")
        saved_name="ARCHIE_SAVED_${var_name}"
        printf -v "$saved_name" '%s' "${!var_name}"
    done < <(compgen -A variable)

    # shellcheck source=/dev/null
    source "$env_file"

    for var_name in "${preexisting_vars[@]}"; do
        saved_name="ARCHIE_SAVED_${var_name}"
        printf -v "$var_name" '%s' "${!saved_name}"
        export "$var_name"
        unset "$saved_name"
    done

    log_info "Loaded overrides from $env_file"
}

handle_help_and_args() {
    local usage_fn="$1"
    shift
    local expected_arg_count="${1:-0}"
    shift || true

    if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
        "$usage_fn"
        exit 0
    fi

    if [[ $# -gt "$expected_arg_count" ]]; then
        log_error "Expected at most $expected_arg_count argument(s), got $#"
        "$usage_fn" >&2
        exit 1
    fi
}

handle_help_and_no_args() {
    handle_help_and_args "$1" 0 "${@:2}"
}

log_step() {
    printf '\n==> %s\n' "$1"
}

log_info() {
    printf '  -> %s\n' "$1"
}

log_warn() {
    printf '  !! %s\n' "$1" >&2
}

log_error() {
    printf '  xx %s\n' "$1" >&2
}

print_command() {
    printf '+'
    for arg in "$@"; do
        printf ' %q' "$arg"
    done
    printf '\n'
}

run_cmd() {
    print_command "$@"
    "$@"
}

run_sudo_cmd() {
    print_command sudo "$@"
    sudo "$@"
}

require_command() {
    local command_name="$1"

    if ! command -v "$command_name" >/dev/null 2>&1; then
        log_error "Missing required command: $command_name"
        exit 1
    fi
}
