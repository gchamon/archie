#!/bin/bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  open-shell.sh

Open an interactive SSH shell for the launched Archie instance.
EOF
}

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/dev-env/common.sh
source "$SCRIPT_DIR/dev-env/common.sh"

handle_help_and_no_args usage "$@"

require_command "incus"
require_command "jq"
require_command "ssh"

load_instance_defaults

if ! instance_exists "$ARCHIE_INSTANCE_NAME"; then
    log_error "Incus instance not found: $ARCHIE_INSTANCE_NAME"
    exit 1
fi

guest_ip="$(resolve_guest_ip "$ARCHIE_INSTANCE_NAME")"

print_command ssh -i "$ARCHIE_INSTANCE_SSH_IDENTITY" \
    "${ARCHIE_INSTANCE_USERNAME}@${guest_ip}"
exec ssh -i "$ARCHIE_INSTANCE_SSH_IDENTITY" \
    "${ARCHIE_INSTANCE_USERNAME}@${guest_ip}"
