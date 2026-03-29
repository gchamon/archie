#!/bin/bash
set -euo pipefail

COMMON_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/bash/lib.sh
source "$COMMON_DIR/../../lib/bash/lib.sh"
load_repo_env_file "$REPO_ROOT/.env.sh" 'ARCHIE_*'

state_root_dir() {
    printf '%s\n' "$REPO_ROOT/.state/dev-env"
}

base_state_dir() {
    printf '%s/%s\n' "$(state_root_dir)" "$ARCHIE_BASE_VM_NAME"
}

instance_state_dir() {
    printf '%s/%s\n' "$(state_root_dir)" "$ARCHIE_INSTANCE_NAME"
}

instance_exists() {
    incus info "$1" >/dev/null 2>&1
}

instance_status() {
    incus info "$1" 2>/dev/null | awk '/^Status:/ { print $2 }'
}

resolve_guest_ip() {
    local instance_name="$1"
    local guest_ip=""

    guest_ip="$(
        incus list "$instance_name" --format json \
            | jq -r --arg vm_name "$instance_name" '
                .[]
                | select(.name == $vm_name)
                | .state.network
                | to_entries[]
                | select(.key != "lo")
                | .value.addresses[]?
                | select(.family == "inet" and .scope != "link")
                | .address
            ' \
            | head -n 1
    )"

    if [[ -z "$guest_ip" ]]; then
        log_error "Unable to resolve a guest IPv4 address for $instance_name"
        exit 1
    fi

    printf '%s\n' "$guest_ip"
}

wait_for_vm_agent() {
    local instance_name="$1"
    local timeout_seconds="${ARCHIE_INCUS_AGENT_TIMEOUT_SECONDS:-300}"
    local interval_seconds="${ARCHIE_INCUS_AGENT_POLL_SECONDS:-2}"
    local start_time=""
    local current_time=""
    local output=""

    start_time="$(date +%s)"

    while true; do
        if output="$(incus exec "$instance_name" -- true 2>&1)"; then
            return 0
        fi

        if [[ "$output" == *"VM agent isn't currently running"* ]]; then
            current_time="$(date +%s)"
            if (( current_time - start_time >= timeout_seconds )); then
                log_error "Timed out waiting for the Incus VM agent in $instance_name"
                printf '%s\n' "$output" >&2
                exit 1
            fi

            sleep "$interval_seconds"
            continue
        fi

        printf '%s\n' "$output" >&2
        exit 1
    done
}

wait_for_cloud_init() {
    local instance_name="$1"

    run_cmd incus exec "$instance_name" -- cloud-init status --wait
}

load_base_defaults() {
    ARCHIE_BASE_VM_NAME="${ARCHIE_BASE_VM_NAME:-archie-dev}"
    ARCHIE_BASE_VM_HOSTNAME="${ARCHIE_BASE_VM_HOSTNAME:-archie-dev}"
    ARCHIE_BASE_VM_USERNAME="${ARCHIE_BASE_VM_USERNAME:-archie}"
    ARCHIE_BASE_SOURCE_IMAGE="${ARCHIE_BASE_SOURCE_IMAGE:-images:archlinux/current/cloud}"
    ARCHIE_BASE_IMAGE_ALIAS="${ARCHIE_BASE_IMAGE_ALIAS:-archie/reproducible-baseline}"
    ARCHIE_BASE_VM_CPU_LIMIT="${ARCHIE_BASE_VM_CPU_LIMIT:-4}"
    ARCHIE_BASE_VM_MEMORY="${ARCHIE_BASE_VM_MEMORY:-8GiB}"
    ARCHIE_BASE_VM_ROOT_DISK_SIZE="${ARCHIE_BASE_VM_ROOT_DISK_SIZE:-32GiB}"
    ARCHIE_BASE_SSH_PUBLIC_KEY_PATH="${ARCHIE_BASE_SSH_PUBLIC_KEY_PATH:-$HOME/.ssh/homelab.pub}"

    if [[ -z "${ARCHIE_BASE_VM_SSH_AUTHORIZED_KEY:-}" ]]; then
        if [[ ! -f "$ARCHIE_BASE_SSH_PUBLIC_KEY_PATH" ]]; then
            log_error "Missing SSH public key file: $ARCHIE_BASE_SSH_PUBLIC_KEY_PATH"
            exit 1
        fi

        ARCHIE_BASE_VM_SSH_AUTHORIZED_KEY="$(< "$ARCHIE_BASE_SSH_PUBLIC_KEY_PATH")"
    fi

    ARCHIE_BASE_VM_PASSWORD_HASH="${ARCHIE_BASE_VM_PASSWORD_HASH:-$(openssl passwd -6 'archie')}"

    export ARCHIE_BASE_VM_NAME
    export ARCHIE_BASE_VM_HOSTNAME
    export ARCHIE_BASE_VM_USERNAME
    export ARCHIE_BASE_SOURCE_IMAGE
    export ARCHIE_BASE_IMAGE_ALIAS
    export ARCHIE_BASE_VM_CPU_LIMIT
    export ARCHIE_BASE_VM_MEMORY
    export ARCHIE_BASE_VM_ROOT_DISK_SIZE
    export ARCHIE_BASE_VM_SSH_AUTHORIZED_KEY
    export ARCHIE_BASE_VM_PASSWORD_HASH
}

load_instance_defaults() {
    ARCHIE_INSTANCE_IMAGE_ALIAS="${ARCHIE_INSTANCE_IMAGE_ALIAS:-archie/reproducible-baseline}"
    ARCHIE_INSTANCE_NAME="${ARCHIE_INSTANCE_NAME:-archie-dev-from-image}"
    ARCHIE_INSTANCE_USERNAME="${ARCHIE_INSTANCE_USERNAME:-archie}"
    ARCHIE_INSTANCE_REPO_URL="${ARCHIE_INSTANCE_REPO_URL:-https://gitlab.com/gabriel.chamon/archie.git}"
    ARCHIE_INSTANCE_SSH_IDENTITY="${ARCHIE_INSTANCE_SSH_IDENTITY:-$HOME/.ssh/homelab}"
    ARCHIE_INSTANCE_MEMORY="${ARCHIE_INSTANCE_MEMORY:-4GiB}"

    export ARCHIE_INSTANCE_IMAGE_ALIAS
    export ARCHIE_INSTANCE_NAME
    export ARCHIE_INSTANCE_USERNAME
    export ARCHIE_INSTANCE_REPO_URL
    export ARCHIE_INSTANCE_SSH_IDENTITY
    export ARCHIE_INSTANCE_MEMORY
}
