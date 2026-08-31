#!/bin/bash

set -euo pipefail

repo_root="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
channel="${ARCHIE_CLI_CHANNEL:-stable}"
version="$(sed -n 's/^version = "\([^"]*\)"/\1/p' "$repo_root/pyproject.toml" | head -1)"

case "$channel" in
    stable)
        package_dir="${ARCHIE_CLI_AUR_DIR:-$repo_root/../archie-cli}"
        [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
            echo "Stable package requires a final project version" >&2
            exit 1
        }
        expected_version="$version"
        ;;
    nightly)
        package_dir="${ARCHIE_CLI_AUR_DIR:-$repo_root/../archie-cli-nightly}"
        [[ "$version" =~ ^([0-9]+\.[0-9]+\.[0-9]+)a[0-9]+$ ]] || {
            echo "Nightly package requires an alpha project version" >&2
            exit 1
        }
        alpha_base="${BASH_REMATCH[1]}"
        commit_count="$(git -C "$repo_root" rev-list --count "$(sed -n 's/^_commit=//p' "$package_dir/PKGBUILD")")"
        expected_version="${alpha_base}a$commit_count"
        ;;
    *)
        echo "ARCHIE_CLI_CHANNEL must be 'stable' or 'nightly'" >&2
        exit 2
        ;;
esac

pkgver="$(sed -n 's/^pkgver=//p' "$package_dir/PKGBUILD")"
commit="$(sed -n 's/^_commit=//p' "$package_dir/PKGBUILD")"

[[ "$expected_version" == "$pkgver" ]] || { echo "PKGBUILD version is incorrect" >&2; exit 1; }
[[ "$(sed -n 's/^pkgrel=//p' "$package_dir/PKGBUILD")" =~ ^[1-9][0-9]*$ ]] || {
    echo "PKGBUILD has an invalid package release" >&2
    exit 1
}
[[ "$commit" =~ ^[0-9a-f]{40}$ ]] || { echo "PKGBUILD has no immutable source commit" >&2; exit 1; }
grep -Fq "/archive/\${_commit}/" "$package_dir/PKGBUILD"
! grep -Fq "SKIP" "$package_dir/PKGBUILD"
cmp <(cd "$package_dir" && makepkg --printsrcinfo) "$package_dir/.SRCINFO"
