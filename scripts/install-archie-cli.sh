#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/bash/lib.sh
source "$SCRIPT_DIR/../lib/bash/lib.sh"

usage() {
    cat <<'EOF'
Usage: ./scripts/install-archie-cli.sh

Build and install archie-cli from this repository checkout.
EOF
}

main() {
    handle_help_and_no_args usage "$@"

    require_command makepkg
    log_step "Install archie-cli from local repository"
    (
        cd "$REPO_ROOT/packaging/archie-cli"
        run_cmd makepkg -Cfsi --noconfirm
    )
}

main "$@"
