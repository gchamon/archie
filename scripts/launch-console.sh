#!/bin/bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  launch-console.sh

Open the Incus VGA console for the launched Archie instance.
EOF
}

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/dev-env/common.sh
source "$SCRIPT_DIR/dev-env/common.sh"

handle_help_and_no_args usage "$@"

require_command "incus"
load_instance_defaults

if ! instance_exists "$ARCHIE_INSTANCE_NAME"; then
    log_error "Incus instance not found: $ARCHIE_INSTANCE_NAME"
    exit 1
fi

print_command incus console --type=vga "$ARCHIE_INSTANCE_NAME"
exec incus console --type=vga "$ARCHIE_INSTANCE_NAME"
