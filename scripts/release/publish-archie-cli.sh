#!/bin/bash

set -euo pipefail

script_dir="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
channel="${ARCHIE_CLI_CHANNEL:-stable}"
commit="${1:-$(git -C "$repo_root" rev-parse HEAD)}"

case "$channel" in
    stable) package_dir="${ARCHIE_CLI_AUR_DIR:-$repo_root/../archie-cli}" ;;
    alpha|nightly|rc) package_dir="${ARCHIE_CLI_AUR_DIR:-$repo_root/../archie-cli-nightly}" ;;
    *) echo "ARCHIE_CLI_CHANNEL must be 'stable', 'rc', or 'alpha'" >&2; exit 2 ;;
esac
remote="${ARCHIE_CLI_AUR_REMOTE:-aur}"

git -C "$package_dir" remote get-url "$remote" >/dev/null 2>&1 || remote=origin
if [[ -z "$(git -C "$package_dir" status --porcelain)" ]]; then
    echo "AUR package is already current"
    exit 0
fi
git -C "$package_dir" add PKGBUILD .SRCINFO
git -C "$package_dir" commit -m "Update archie-cli $channel for ${commit:0:12}"
git -C "$package_dir" push "$remote" HEAD:master
