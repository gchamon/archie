#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/bash/lib.sh
source "$SCRIPT_DIR/../lib/bash/lib.sh"

usage() {
    cat <<'EOF'
Usage: ./scripts/install-archie-cli.sh

Build and install archie-cli from this checkout's local PKGBUILD.
EOF
}

main() {
    handle_help_and_no_args usage "$@"

    if [[ ! -f "$REPO_ROOT/packaging/archie-cli/PKGBUILD" ]]; then
        log_error "Could not find packaging/archie-cli/PKGBUILD in $REPO_ROOT"
        exit 1
    fi

    require_command makepkg
    log_step "Install archie-cli from local package"

    if pacman -Q archie-cli >/dev/null 2>&1; then
        log_info "archie-cli is already installed; reinstalling to pick up latest build"
    fi

    (
        cd "$REPO_ROOT/packaging/archie-cli"
        run_cmd makepkg -Cfsi --noconfirm
    )
}

main "$@"
