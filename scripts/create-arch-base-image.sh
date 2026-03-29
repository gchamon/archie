#!/bin/bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  create-arch-base-image.sh

Create the reproducible Archie base image from the documented Incus bootstrap
flow. Set ARCHIE_BASE_* variables in ./.env.sh or on the command line if you
need overrides.
EOF
}

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/dev-env/common.sh
source "$SCRIPT_DIR/dev-env/common.sh"

handle_help_and_no_args usage "$@"

require_command "envsubst"
require_command "incus"
require_command "jq"
require_command "openssl"

load_base_defaults

if instance_exists "$ARCHIE_BASE_VM_NAME"; then
    log_error "Incus instance already exists: $ARCHIE_BASE_VM_NAME"
    exit 1
fi

log_step "Render bootstrap cloud-init"
run_cmd mkdir -p "$(base_state_dir)"
envsubst < "$REPO_ROOT/templates/dev-env/cloud-init/user-data.yaml.tpl" \
    > "$(base_state_dir)/user-data.yaml"

log_step "Create bootstrap VM"
run_cmd incus init "$ARCHIE_BASE_SOURCE_IMAGE" "$ARCHIE_BASE_VM_NAME" --vm \
    --config limits.cpu="$ARCHIE_BASE_VM_CPU_LIMIT" \
    --config limits.memory="$ARCHIE_BASE_VM_MEMORY"

run_cmd incus config set "$ARCHIE_BASE_VM_NAME" cloud-init.user-data - < "$(base_state_dir)/user-data.yaml"
run_cmd incus config device override "$ARCHIE_BASE_VM_NAME" root size="$ARCHIE_BASE_VM_ROOT_DISK_SIZE"

log_step "Start bootstrap VM"
run_cmd incus start "$ARCHIE_BASE_VM_NAME"

log_step "Wait for the Incus VM agent"
wait_for_vm_agent "$ARCHIE_BASE_VM_NAME"

log_step "Wait for cloud-init"
wait_for_cloud_init "$ARCHIE_BASE_VM_NAME"

log_step "Stop bootstrap VM"
run_cmd incus stop "$ARCHIE_BASE_VM_NAME"

log_step "Publish base image"
run_cmd incus publish "$ARCHIE_BASE_VM_NAME" \
    --alias "$ARCHIE_BASE_IMAGE_ALIAS" \
    --reuse \
    "archie.base_image=$ARCHIE_BASE_SOURCE_IMAGE"

printf '\nPublished image alias: %s\n' "$ARCHIE_BASE_IMAGE_ALIAS"
printf 'Next: ./scripts/launch-archie-instance.sh\n'
