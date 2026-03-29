#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/bash/lib.sh
source "$SCRIPT_DIR/../../lib/bash/lib.sh"
load_repo_env_file "$REPO_ROOT/.env.sh" 'ARCHIE_*'

usage() {
    cat <<'EOF'
Usage:
  ssh-clipboard-sync.sh [--identity PATH] [--interval SECONDS] <user@host>

Start a bidirectional text clipboard bridge between the local Wayland session
and a remote Wayland guest reachable over SSH.
EOF
}

file_hash() {
    sha256sum "$1" | awk '{print $1}'
}

resolve_local_wayland() {
    local runtime_dir="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
    local display_name="${WAYLAND_DISPLAY:-}"
    local candidate=""

    if [[ -n "$display_name" && -S "$runtime_dir/$display_name" ]]; then
        printf '%s\n%s\n' "$runtime_dir" "$display_name"
        return 0
    fi

    for candidate in "$runtime_dir"/wayland-*; do
        if [[ -S "$candidate" ]]; then
            printf '%s\n%s\n' "$runtime_dir" "$(basename "$candidate")"
            return 0
        fi
    done

    log_error "Unable to find a local Wayland socket under $runtime_dir"
    return 1
}

resolve_remote_wayland() {
    "${SSH_CMD[@]}" '
runtime_dir="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
display_name="${WAYLAND_DISPLAY:-}"

if [ -n "$display_name" ] && [ -S "$runtime_dir/$display_name" ]; then
    printf "%s\n%s\n" "$runtime_dir" "$display_name"
    exit 0
fi

for candidate in "$runtime_dir"/wayland-*; do
    if [ -S "$candidate" ]; then
        basename_candidate="$(basename "$candidate")"
        printf "%s\n%s\n" "$runtime_dir" "$basename_candidate"
        exit 0
    fi
done

exit 1
'
}

describe_remote_wayland_failure() {
    local ssh_target="$1"

    # Heuristic: if SSH works and wl-clipboard is installed but no Wayland
    # socket is visible under the remote runtime dir, the usual cause is that
    # the target user has not logged into Hyprland yet. This is more helpful
    # than surfacing a generic "could not resolve socket" error.
    log_error "Unable to resolve the remote Wayland runtime and display for $ssh_target"
    log_info "Log into Hyprland as that user in SDDM first, then rerun this command"
}

capture_host_clipboard() {
    local local_runtime_dir=""
    local local_wayland_display=""

    mapfile -t local_wayland_info < <(resolve_local_wayland)
    if ((${#local_wayland_info[@]} < 2)); then
        log_error "Unable to resolve the local Wayland runtime and display"
        exit 1
    fi
    local_runtime_dir="${local_wayland_info[0]}"
    local_wayland_display="${local_wayland_info[1]}"

    if ! XDG_RUNTIME_DIR="$local_runtime_dir" WAYLAND_DISPLAY="$local_wayland_display" \
        wl-paste >"$HOST_CLIPBOARD_FILE" 2>/dev/null; then
        : >"$HOST_CLIPBOARD_FILE"
    fi
}

capture_guest_clipboard() {
    if ! "${SSH_CMD[@]}" \
        "XDG_RUNTIME_DIR=\"$REMOTE_RUNTIME_DIR\" WAYLAND_DISPLAY=\"$REMOTE_WAYLAND_DISPLAY\" wl-paste" \
        >"$GUEST_CLIPBOARD_FILE" 2>/dev/null; then
        : >"$GUEST_CLIPBOARD_FILE"
    fi
}

require_command "awk"
require_command "sha256sum"
require_command "ssh"
require_command "wl-copy"
require_command "wl-paste"

SSH_IDENTITY="${ARCHIE_CLIPBOARD_SYNC_IDENTITY:-}"
INTERVAL_SECONDS="${ARCHIE_CLIPBOARD_SYNC_INTERVAL_SECONDS:-1}"
SSH_TARGET=""

while [[ $# -gt 0 ]]; do
    case "$1" in
    --identity)
        SSH_IDENTITY="$2"
        shift 2
        ;;
    --interval)
        INTERVAL_SECONDS="$2"
        shift 2
        ;;
    -h | --help)
        usage
        exit 0
        ;;
    -*)
        log_error "Unknown option: $1"
        usage >&2
        exit 1
        ;;
    *)
        if [[ -n "$SSH_TARGET" ]]; then
            log_error "Only one SSH target may be provided."
            usage >&2
            exit 1
        fi

        SSH_TARGET="$1"
        shift
        ;;
    esac
done

if [[ -z "$SSH_TARGET" ]]; then
    log_error "Missing SSH target."
    usage >&2
    exit 1
fi

SSH_CMD=(
    ssh
    -o BatchMode=yes
    -o ConnectTimeout=5
)

if [[ -n "$SSH_IDENTITY" ]]; then
    SSH_CMD+=(-i "$SSH_IDENTITY")
fi

SSH_CMD+=("$SSH_TARGET")

run_cmd "${SSH_CMD[@]}" 'command -v wl-copy >/dev/null 2>&1 && command -v wl-paste >/dev/null 2>&1'

mapfile -t remote_wayland_info < <(resolve_remote_wayland)
if ((${#remote_wayland_info[@]} < 2)); then
    describe_remote_wayland_failure "$SSH_TARGET"
    exit 1
fi
REMOTE_RUNTIME_DIR="${remote_wayland_info[0]}"
REMOTE_WAYLAND_DISPLAY="${remote_wayland_info[1]}"

HOST_CLIPBOARD_FILE="$(mktemp)"
GUEST_CLIPBOARD_FILE="$(mktemp)"
trap 'rm -f "$HOST_CLIPBOARD_FILE" "$GUEST_CLIPBOARD_FILE"' EXIT

LAST_HOST_HASH=""
LAST_GUEST_HASH=""

while true; do
    capture_host_clipboard
    capture_guest_clipboard

    HOST_HASH="$(file_hash "$HOST_CLIPBOARD_FILE")"
    GUEST_HASH="$(file_hash "$GUEST_CLIPBOARD_FILE")"

    if [[ "$HOST_HASH" != "$LAST_HOST_HASH" && "$HOST_HASH" != "$GUEST_HASH" ]]; then
        "${SSH_CMD[@]}" \
            "XDG_RUNTIME_DIR=\"$REMOTE_RUNTIME_DIR\" WAYLAND_DISPLAY=\"$REMOTE_WAYLAND_DISPLAY\" wl-copy" \
            <"$HOST_CLIPBOARD_FILE"
        LAST_HOST_HASH="$HOST_HASH"
        LAST_GUEST_HASH="$HOST_HASH"
    elif [[ "$GUEST_HASH" != "$LAST_GUEST_HASH" && "$GUEST_HASH" != "$HOST_HASH" ]]; then
        mapfile -t local_wayland_info < <(resolve_local_wayland)
        if ((${#local_wayland_info[@]} < 2)); then
            log_error "Unable to resolve the local Wayland runtime and display"
            exit 1
        fi
        XDG_RUNTIME_DIR="${local_wayland_info[0]}" WAYLAND_DISPLAY="${local_wayland_info[1]}" \
            wl-copy <"$GUEST_CLIPBOARD_FILE"
        LAST_HOST_HASH="$GUEST_HASH"
        LAST_GUEST_HASH="$GUEST_HASH"
    else
        LAST_HOST_HASH="$HOST_HASH"
        LAST_GUEST_HASH="$GUEST_HASH"
    fi

    sleep "$INTERVAL_SECONDS"
done
