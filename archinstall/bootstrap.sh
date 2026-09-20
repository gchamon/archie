#!/bin/bash

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: bootstrap.sh --repository URL --revision SHA --username USER
EOF
}

die() {
    printf 'Archie bootstrap failed: %s\n' "$1" >&2
    exit 1
}

parse_args() {
    repository=""
    revision=""
    username=""

    while (($#)); do
        case "$1" in
            --repository)
                repository="${2:-}"
                shift 2
                ;;
            --revision)
                revision="${2:-}"
                shift 2
                ;;
            --username)
                username="${2:-}"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                usage >&2
                die "Unknown argument: $1"
                ;;
        esac
    done

    [[ "$repository" =~ ^https://[^[:space:]]+\.git$ ]] || die "Invalid repository URL"
    [[ "$revision" =~ ^[0-9a-f]{40}$ ]] || die "Revision must be a full commit SHA"
    [[ "$username" =~ ^[a-z_][a-z0-9_-]*$ ]] || die "Invalid target username"
    (( EUID == 0 )) || die "Bootstrap must run as root"
    home="/home/$username"
}

run_as_target() {
    runuser -u "$username" -- env HOME="$home" USER="$username" "$@"
}

checkout_archie() {
    local checkout="$home/archie"
    local actual=""
    local target_uid="$(id -u "$username")"
    local target_gid="$(id -g "$username")"

    install -d -m 0755 -o "$target_uid" -g "$target_gid" "$home"

    if [[ -e "$checkout" ]]; then
        [[ -d "$checkout/.git" ]] || die "Existing Archie path is not a Git checkout"
        actual="$(run_as_target git -C "$checkout" rev-parse HEAD)"
        [[ "$actual" == "$revision" ]] || die "Existing Archie checkout has revision $actual"
    else
        run_as_target git init "$checkout"
        run_as_target git -C "$checkout" remote add origin "$repository"
        run_as_target git -C "$checkout" fetch --depth=1 origin "$revision"
        run_as_target git -C "$checkout" checkout --detach FETCH_HEAD
    fi

    actual="$(run_as_target git -C "$checkout" rev-parse HEAD)"
    [[ "$actual" == "$revision" ]] || die "Archie checkout has revision $actual"

    bash "$checkout/archinstall/provision.sh" \
        --username "$username"
}

parse_args "$@"
checkout_archie
