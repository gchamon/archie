#!/bin/bash

set -euo pipefail

repo_root="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
channel="${ARCHIE_CLI_CHANNEL:-stable}"
version="$(sed -n 's/^version = "\([^"]*\)"/\1/p' "$repo_root/pyproject.toml" | head -1)"

case "$channel" in
    stable)
        package_dir="${ARCHIE_CLI_AUR_DIR:-$repo_root/../archie-cli}"
        expected_version="$version"
        ;;
    alpha|nightly|rc)
        package_dir="${ARCHIE_CLI_AUR_DIR:-$repo_root/../archie-cli-nightly}"
        [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
            echo "CI prerelease package requires a stable project version" >&2
            exit 1
        }
        marker="$channel"
        [[ "$marker" == alpha || "$marker" == nightly ]] && marker=a
        expected_version="${version}${marker}"
        ;;
    *)
        echo "ARCHIE_CLI_CHANNEL must be 'stable', 'rc', or 'alpha'" >&2
        exit 2
        ;;
esac

pkgver="$(sed -n 's/^pkgver=//p' "$package_dir/PKGBUILD")"
pkgrel="$(sed -n 's/^pkgrel=//p' "$package_dir/PKGBUILD")"
commit="$(sed -n 's/^_commit=//p' "$package_dir/PKGBUILD")"

[[ "$expected_version" == "$pkgver" ]] || { echo "PKGBUILD version is incorrect" >&2; exit 1; }
[[ "$(sed -n 's/^pkgrel=//p' "$package_dir/PKGBUILD")" =~ ^[1-9][0-9]*$ ]] || {
    echo "PKGBUILD has an invalid package release" >&2
    exit 1
}
[[ "$commit" =~ ^[0-9a-f]{40}$ ]] || { echo "PKGBUILD has no immutable source commit" >&2; exit 1; }
if [[ -n "${ARCHIE_CLI_PACKAGE_RELEASE:-}" ]]; then
    [[ "$pkgrel" == "$ARCHIE_CLI_PACKAGE_RELEASE" ]] || {
        echo "PKGBUILD release does not match the CI package release" >&2
        exit 1
    }
fi
grep -Fq "git+https://gitlab.com/gabriel.chamon/archie.git#commit=\${_commit}" "$package_dir/PKGBUILD"
grep -Fq "sha256sums=('SKIP')" "$package_dir/PKGBUILD"
cmp <(cd "$package_dir" && makepkg --printsrcinfo) "$package_dir/.SRCINFO"
