#!/bin/bash

set -euo pipefail

repo_root="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
channel="${ARCHIE_CLI_CHANNEL:-stable}"
commit="${1:-$(git -C "$repo_root" rev-parse HEAD)}"
version="$(sed -n 's/^version = "\([^"]*\)"/\1/p' "$repo_root/pyproject.toml" | head -1)"

[[ "$commit" =~ ^[0-9a-f]{40}$ ]] || { echo "Invalid source commit: $commit" >&2; exit 1; }

case "$channel" in
    stable)
        package_dir="${ARCHIE_CLI_AUR_DIR:-$repo_root/../archie-cli}"
        template="$repo_root/packaging/archie-cli/PKGBUILD.aur"
        [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
            echo "Stable publishing requires a final project version" >&2
            exit 1
        }
        package_version="$version"
        ;;
    nightly)
        package_dir="${ARCHIE_CLI_AUR_DIR:-$repo_root/../archie-cli-nightly}"
        template="$repo_root/packaging/archie-cli/PKGBUILD.nightly.aur"
        [[ "$version" =~ ^([0-9]+\.[0-9]+\.[0-9]+)a[0-9]+$ ]] || {
            echo "Nightly publishing requires an alpha project version" >&2
            exit 1
        }
        alpha_base="${BASH_REMATCH[1]}"
        package_version="${alpha_base}a$(git -C "$repo_root" rev-list --count "$commit")"
        ;;
    *)
        echo "ARCHIE_CLI_CHANNEL must be 'stable' or 'nightly'" >&2
        exit 2
        ;;
esac

[[ -d "$package_dir/.git" ]] || { echo "AUR checkout not found at $package_dir" >&2; exit 1; }
[[ -f "$template" ]] || { echo "AUR PKGBUILD template not found at $template" >&2; exit 1; }

current_version=""
current_release="0"
if [[ -f "$package_dir/PKGBUILD" ]]; then
    current_version="$(sed -n 's/^pkgver=//p' "$package_dir/PKGBUILD")"
    current_release="$(sed -n 's/^pkgrel=//p' "$package_dir/PKGBUILD")"
fi
[[ "$current_release" =~ ^[1-9][0-9]*$ ]] || current_release=0
if [[ "$package_version" == "$current_version" ]]; then
    package_release=$((current_release + 1))
else
    package_release=1
fi

archive="$(mktemp)"
trap 'rm -f "$archive"' EXIT
archive_url="https://gitlab.com/gabriel.chamon/archie/-/archive/$commit/archie-$commit.tar.gz"
if [[ -n "${ARCHIE_CLI_ARCHIVE_FILE:-}" ]]; then
    [[ -f "$ARCHIE_CLI_ARCHIVE_FILE" ]] || {
        echo "Archive override does not exist: $ARCHIE_CLI_ARCHIVE_FILE" >&2
        exit 1
    }
    cp "$ARCHIE_CLI_ARCHIVE_FILE" "$archive"
else
    curl -L --fail --silent --show-error "$archive_url" -o "$archive"
fi
checksum="$(sha256sum "$archive" | awk '{print $1}')"

cp "$template" "$package_dir/PKGBUILD"
sed -i \
    -e "s/^pkgver=.*/pkgver=$package_version/" \
    -e "s/^pkgrel=.*/pkgrel=$package_release/" \
    -e "s/^_commit=.*/_commit=$commit/" \
    -e "s/^sha256sums=.*/sha256sums=('$checksum')/" \
    "$package_dir/PKGBUILD"
(
    cd "$package_dir"
    makepkg --printsrcinfo > .SRCINFO
)
