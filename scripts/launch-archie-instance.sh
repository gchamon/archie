#!/bin/bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  launch-archie-instance.sh

Launch an Archie VM instance from the published reproducible image. Set
ARCHIE_INSTANCE_* variables in ./.env.sh or on the command line if you need
overrides.
EOF
}

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/dev-env/common.sh
source "$SCRIPT_DIR/dev-env/common.sh"

handle_help_and_no_args usage "$@"

require_command "cp"
require_command "envsubst"
require_command "incus"
require_command "jq"

load_instance_defaults

if instance_exists "$ARCHIE_INSTANCE_NAME"; then
    log_error "Incus instance already exists: $ARCHIE_INSTANCE_NAME"
    exit 1
fi

log_step "Render launch-time cloud-init"
run_cmd mkdir -p "$(instance_state_dir)"
envsubst < "$REPO_ROOT/templates/dev-env/cloud-init/archie-instance-user-data.yaml.tpl" \
    > "$(instance_state_dir)/archie-instance-user-data.yaml"

run_cmd cp "$REPO_ROOT/templates/dev-env/incus/archie-instance-raw-qemu.conf" \
    "$(instance_state_dir)/archie-instance-raw-qemu.conf"

log_step "Create Archie instance"
run_cmd incus init "$ARCHIE_INSTANCE_IMAGE_ALIAS" "$ARCHIE_INSTANCE_NAME" --vm \
    --config limits.memory="$ARCHIE_INSTANCE_MEMORY"

run_cmd incus config set "$ARCHIE_INSTANCE_NAME" raw.qemu.conf - \
    < "$(instance_state_dir)/archie-instance-raw-qemu.conf"
run_cmd incus config set "$ARCHIE_INSTANCE_NAME" cloud-init.user-data - \
    < "$(instance_state_dir)/archie-instance-user-data.yaml"

log_step "Start Archie instance"
run_cmd incus start "$ARCHIE_INSTANCE_NAME"

log_step "Wait for the Incus VM agent"
wait_for_vm_agent "$ARCHIE_INSTANCE_NAME"

log_step "Wait for cloud-init"
wait_for_cloud_init "$ARCHIE_INSTANCE_NAME"

guest_ip="$(resolve_guest_ip "$ARCHIE_INSTANCE_NAME")"

printf '\nGuest IP: %s\n' "$guest_ip"
printf 'Next: ./scripts/launch-console.sh\n'
printf 'Next: ./scripts/open-shell.sh\n'
printf 'Next: ./scripts/setup-shared-clipboard.sh\n'
