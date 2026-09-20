#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
PLUGIN="$ROOT/archinstall/plugin.py"

mode="${1:-}"
first_argument="${2:-}"

[[ "$mode" == "development" || "$mode" == "release" ]] || {
    printf 'Usage: %s development REF\n' "$0" >&2
    printf '       %s release RELEASE\n' "$0" >&2
    exit 2
}

plugin_release="$(sed -n 's/^ARCHIE_RELEASE:.*= \(.*\)$/\1/p' "$PLUGIN")"
plugin_development_ref="$(sed -n 's/^ARCHIE_DEVELOPMENT_REF = "\([^"]*\)"/\1/p' "$PLUGIN")"

[[ -n "$plugin_development_ref" ]] || {
    printf 'Plugin development ref is missing\n' >&2
    exit 1
}

if [[ "$mode" == "development" ]]; then
    [[ "$plugin_release" == "None" ]] || {
        printf 'Development plugin must set ARCHIE_RELEASE to None\n' >&2
        exit 1
    }
    [[ "$plugin_development_ref" == "$first_argument" ]] || {
        printf 'Plugin development ref is %s, expected %s\n' \
            "$plugin_development_ref" "$first_argument" >&2
        exit 1
    }
    repository_ref="$plugin_development_ref"
    label="development ref $repository_ref"
else
    [[ "$plugin_release" == "\"$first_argument\"" ]] || {
        printf 'Plugin release is %s, expected "%s"\n' "$plugin_release" "$first_argument" >&2
        exit 1
    }
    repository_ref="$first_argument"
    label="release $first_argument"
fi

git -C "$ROOT" rev-parse --verify "${repository_ref}^{commit}" >/dev/null
git -C "$ROOT" show "$repository_ref:archinstall/package-manifest.json" | jq empty
git -C "$ROOT" cat-file -e "$repository_ref:archinstall/bootstrap.sh" || {
    printf 'Repository ref does not contain archinstall/bootstrap.sh: %s\n' \
        "$repository_ref" >&2
    exit 1
}
git -C "$ROOT" show "$repository_ref:archinstall/bootstrap.sh" | bash -n
printf 'Archinstall plugin metadata is consistent for %s\n' "$label"
