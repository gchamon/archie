#!/bin/bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  cleanup-archie-instance.sh

Delete the launched Archie instance and its rendered launch-state files. This
does not touch the base image alias or bootstrap VM.
EOF
}

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/dev-env/common.sh
source "$SCRIPT_DIR/dev-env/common.sh"

handle_help_and_no_args usage "$@"

require_command "incus"
load_instance_defaults

if instance_exists "$ARCHIE_INSTANCE_NAME"; then
    if [[ "$(instance_status "$ARCHIE_INSTANCE_NAME")" == "RUNNING" ]]; then
        log_info "Stopping instance $ARCHIE_INSTANCE_NAME"
        incus stop "$ARCHIE_INSTANCE_NAME"
    fi

    log_info "Deleting instance $ARCHIE_INSTANCE_NAME"
    incus delete "$ARCHIE_INSTANCE_NAME"
else
    log_info "Instance not found: $ARCHIE_INSTANCE_NAME"
fi

if [[ -d "$(instance_state_dir)" ]]; then
    log_step "Remove launch state directory"
    run_cmd rm -rf "$(instance_state_dir)"
fi

printf '\nCleaned up instance: %s\n' "$ARCHIE_INSTANCE_NAME"
