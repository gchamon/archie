#!/bin/bash

set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  push-github-mirror.sh branch <branch-name>
  push-github-mirror.sh tag <tag-name>

Required environment variables:
  GITHUB_MIRROR_SSH_URL
  GITHUB_DEPLOY_KEY_B64

Optional environment variables:
  GITHUB_MIRROR_KNOWN_HOSTS
EOF
}

require_env() {
    local name="$1"

    if [[ -z "${!name:-}" ]]; then
        echo "Missing required environment variable: ${name}" >&2
        exit 1
    fi
}

setup_known_hosts() {
    local known_hosts_path="$1"

    if [[ -n "${GITHUB_MIRROR_KNOWN_HOSTS:-}" ]]; then
        printf '%s\n' "$GITHUB_MIRROR_KNOWN_HOSTS" >"$known_hosts_path"
        return
    fi

    ssh-keyscan github.com >"$known_hosts_path" 2>/dev/null
}

setup_ssh_key() {
    local key_path="$1"

    printf '%s' "$GITHUB_DEPLOY_KEY_B64" | base64 -d >"$key_path"
    chmod 600 "$key_path"
}

configure_remote() {
    local remote_name="$1"

    if git remote get-url "$remote_name" >/dev/null 2>&1; then
        git remote set-url "$remote_name" "$GITHUB_MIRROR_SSH_URL"
        return
    fi

    git remote add "$remote_name" "$GITHUB_MIRROR_SSH_URL"
}

push_branch() {
    local remote_name="$1"
    local branch_name="$2"

    git push "$remote_name" "HEAD:refs/heads/${branch_name}"
}

push_tag() {
    local remote_name="$1"
    local tag_name="$2"

    git push "$remote_name" "refs/tags/${tag_name}:refs/tags/${tag_name}"
}

main() {
    local ref_type="${1:-}"
    local ref_name="${2:-}"
    local remote_name="github-mirror"
    local tmp_dir="$(mktemp -d)"
    local key_path="${tmp_dir}/github-mirror"
    local known_hosts_path="${tmp_dir}/known_hosts"

    if [[ -z "$ref_type" || -z "$ref_name" ]]; then
        usage >&2
        exit 1
    fi

    case "$ref_type" in
    branch | tag) ;;
    *)
        usage >&2
        exit 1
        ;;
    esac

    require_env GITHUB_MIRROR_SSH_URL
    require_env GITHUB_DEPLOY_KEY_B64

    trap "rm -rf $tmp_dir" EXIT

    setup_ssh_key "$key_path"
    setup_known_hosts "$known_hosts_path"
    configure_remote "$remote_name"

    export GIT_SSH_COMMAND="ssh -i ${key_path} -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=${known_hosts_path}"

    case "$ref_type" in
    branch)
        push_branch "$remote_name" "$ref_name"
        ;;
    tag)
        push_tag "$remote_name" "$ref_name"
        ;;
    esac
}

main "$@"
