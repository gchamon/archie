#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/bash/lib.sh
source "$SCRIPT_DIR/../lib/bash/lib.sh"

usage() {
    cat <<'EOF'
Usage: ./scripts/install-archie-cli.sh

Install archie-cli from AUR, or use ARCHIE_CLI_SOURCE=local to force a local build.
EOF
}

main() {
    handle_help_and_no_args usage "$@"

    case "${ARCHIE_CLI_SOURCE:-aur}" in
        aur)
            require_command yay
            log_step "Install archie-cli from AUR"
            run_cmd yay -S --needed --noconfirm archie-cli
            ;;
        local)
            require_command makepkg
            log_step "Install archie-cli from local package"
            (
                cd "$REPO_ROOT/packaging/archie-cli"
                run_cmd makepkg -Cfsi --noconfirm
            )
            ;;
        *)
            log_error "ARCHIE_CLI_SOURCE must be 'aur' or 'local'"
            exit 2
            ;;
    esac
}

main "$@"
