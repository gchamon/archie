#!/bin/bash

set -euo pipefail

repo_root="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
channel="${ARCHIE_CLI_CHANNEL:-stable}"
commit="${1:-$(git -C "$repo_root" rev-parse HEAD)}"
version="$(sed -n 's/^version = "\([^"]*\)"/\1/p' "$repo_root/pyproject.toml" | head -1)"

[[ "$commit" =~ ^[0-9a-f]{40}$ ]] || { echo "Invalid source commit: $commit" >&2; exit 1; }
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
    echo "Project version must be a stable semantic version" >&2
    exit 1
}

case "$channel" in
    stable)
        package_dir="${ARCHIE_CLI_AUR_DIR:-$repo_root/../archie-cli}"
        template="$repo_root/packaging/archie-cli/PKGBUILD.aur"
        package_version="$version"
        ;;
    alpha|nightly|rc)
        package_dir="${ARCHIE_CLI_AUR_DIR:-$repo_root/../archie-cli-nightly}"
        template="$repo_root/packaging/archie-cli/PKGBUILD.nightly.aur"
        marker="$channel"
        [[ "$marker" == alpha || "$marker" == nightly ]] && marker=a
        package_version="${version}${marker}"
        ;;
    *)
        echo "ARCHIE_CLI_CHANNEL must be 'stable', 'rc', or 'alpha'" >&2
        exit 2
        ;;
esac

[[ -d "$package_dir/.git" ]] || { echo "AUR checkout not found at $package_dir" >&2; exit 1; }
[[ -f "$template" ]] || { echo "AUR PKGBUILD template not found at $template" >&2; exit 1; }

current_version=""
current_release="0"
current_commit=""
if [[ -f "$package_dir/PKGBUILD" ]]; then
    current_version="$(sed -n 's/^pkgver=//p' "$package_dir/PKGBUILD")"
    current_release="$(sed -n 's/^pkgrel=//p' "$package_dir/PKGBUILD")"
    current_commit="$(sed -n 's/^_commit=//p' "$package_dir/PKGBUILD")"
fi
[[ "$current_release" =~ ^[1-9][0-9]*$ ]] || current_release=0
if [[ "$channel" != stable && "${ARCHIE_CLI_PACKAGE_RELEASE:-}" =~ ^[1-9][0-9]*$ ]]; then
    package_release="$ARCHIE_CLI_PACKAGE_RELEASE"
elif [[ "$package_version" == "$current_version" && "$commit" == "$current_commit" && "$current_release" != 0 ]]; then
    package_release="$current_release"
elif [[ "$package_version" == "$current_version" ]]; then
    package_release=$((current_release + 1))
else
    package_release=1
fi

cp "$template" "$package_dir/PKGBUILD"
sed -i \
    -e "s/^pkgver=.*/pkgver=$package_version/" \
    -e "s/^pkgrel=.*/pkgrel=$package_release/" \
    -e "s/^_commit=.*/_commit=$commit/" \
    "$package_dir/PKGBUILD"
(
    cd "$package_dir"
    makepkg --printsrcinfo > .SRCINFO
)
