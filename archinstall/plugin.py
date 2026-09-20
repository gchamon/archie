"""Archie desktop profile for Archinstall 4.4.

This file is intentionally self-contained because Archinstall downloads a
plugin URL into a temporary file before importing it.
"""

from __future__ import annotations

import json
import re
import shlex
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from archinstall.default_profiles.profile import (
    DisplayServerType,
    GreeterType,
    Profile,
    ProfileType,
)
from archinstall.lib.log import info
from archinstall.lib.profile.profiles_handler import profile_handler

__archinstall__version__ = 4.4
ARCHINSTALL_MIN_VERSION = (4, 4)
ARCHINSTALL_MAX_VERSION = (4, 5)
ARCHIE_REPOSITORY = "https://gitlab.com/gabriel.chamon/archie.git"
# Development mode follows this branch, resolving it to one commit when the
# plugin loads. Release builds use ARCHIE_RELEASE as their repository ref.
ARCHIE_RELEASE: str | None = None
ARCHIE_DEVELOPMENT_REF = "feature/archinstall-desktop"
BOOTSTRAP_REPOSITORY_PATH = "archinstall/bootstrap.sh"
BOOTSTRAP_TARGET_PATH = Path("/root/archie-bootstrap.sh")


class ArchiePluginError(RuntimeError):
    """An Archie-specific installation failure."""


def version_tuple(version: str) -> tuple[int, int]:
    parts = version.split(".")
    try:
        return int(parts[0]), int(parts[1])
    except (IndexError, ValueError) as error:
        raise ArchiePluginError(f"Unable to parse Archinstall version: {version}") from error


def validate_archie_revision(revision: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ArchiePluginError(
            "Archie revision must be a full 40-character lowercase Git commit SHA."
        )


def configured_repository_ref() -> str:
    return ARCHIE_RELEASE or ARCHIE_DEVELOPMENT_REF


def repository_commits_url(ref: str) -> str:
    query = urllib.parse.urlencode({"ref_name": ref, "per_page": 1})
    return (
        "https://gitlab.com/api/v4/projects/gabriel.chamon%2Farchie/"
        f"repository/commits?{query}"
    )


def repository_file_url(path: str, revision: str) -> str:
    encoded_path = urllib.parse.quote(path, safe="")
    encoded_revision = urllib.parse.quote(revision, safe="")
    return (
        "https://gitlab.com/api/v4/projects/gabriel.chamon%2Farchie/"
        f"repository/files/{encoded_path}/raw?ref="
        f"{encoded_revision}"
    )


def validate_archinstall_version(version: str) -> None:
    current = version_tuple(version)
    if not ARCHINSTALL_MIN_VERSION <= current < ARCHINSTALL_MAX_VERSION:
        supported = ".".join(str(part) for part in ARCHINSTALL_MIN_VERSION)
        maximum = ".".join(str(part) for part in ARCHINSTALL_MAX_VERSION)
        raise ArchiePluginError(
            f"Archie requires Archinstall >= {supported} and < {maximum}; "
            f"found {version}. No Archie provisioning was started."
        )


def validate_administrative_users(users: list[Any]) -> Any:
    administrators = [user for user in users if user.sudo]
    if len(administrators) != 1:
        raise ArchiePluginError(
            "Archie requires exactly one administrative user; "
            f"Archinstall supplied {len(administrators)}."
        )
    return administrators[0]


def resolve_revision(ref: str) -> str:
    url = repository_commits_url(ref)
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            commits = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError) as error:
        raise ArchiePluginError(
            f"Could not resolve Archie repository ref {ref} from {url}: {error}"
        ) from error
    if not isinstance(commits, list) or not commits or not isinstance(commits[0], dict):
        raise ArchiePluginError(f"Repository ref resolved to no commit: {url}")
    revision = commits[0].get("id")
    if not isinstance(revision, str):
        raise ArchiePluginError(f"Repository ref response has no commit SHA: {url}")
    validate_archie_revision(revision)
    return revision


def load_repository_file(path: str, revision: str) -> str:
    url = repository_file_url(path, revision)
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode("utf-8")
    except (OSError, ValueError) as error:
        raise ArchiePluginError(
            f"Could not load Archie repository file {path} from {url}: {error}"
        ) from error
    if not content:
        raise ArchiePluginError(f"Repository file is empty: {url}")
    return content


def load_manifest(revision: str) -> dict[str, Any]:
    url = repository_file_url("archinstall/package-manifest.json", revision)
    try:
        manifest = json.loads(load_repository_file("archinstall/package-manifest.json", revision))
    except json.JSONDecodeError as error:
        raise ArchiePluginError(
            f"Could not parse the Archie package manifest from {url}: {error}"
        ) from error

    if manifest.get("schema") != 1:
        raise ArchiePluginError("Unsupported Archie package manifest schema")
    validate_manifest(manifest)
    return manifest


def load_bootstrap_script(revision: str) -> str:
    script = load_repository_file(BOOTSTRAP_REPOSITORY_PATH, revision)
    if not script.startswith("#!/bin/bash\n"):
        raise ArchiePluginError("Archie bootstrap script must start with a Bash shebang")
    return script


def validate_manifest(manifest: dict[str, Any]) -> None:
    required_keys = {
        "schema",
        "official_runtime",
        "aur_runtime",
        "build_dependencies",
        "optional_features",
    }
    missing_keys = required_keys - manifest.keys()
    if missing_keys:
        raise ArchiePluginError(
            "Archie package manifest is missing: " + ", ".join(sorted(missing_keys))
        )

    for key in ("official_runtime", "aur_runtime", "build_dependencies"):
        values = manifest[key]
        if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
            raise ArchiePluginError(f"Package manifest field {key} must contain package names")
        if len(values) != len(set(values)):
            raise ArchiePluginError(f"Package manifest contains duplicate values in {key}")

    official = set(manifest["official_runtime"]) | set(manifest["build_dependencies"])
    aur = set(manifest["aur_runtime"])
    overlap = official & aur
    if overlap:
        raise ArchiePluginError(
            "Packages cannot be both official and AUR packages: "
            + ", ".join(sorted(overlap))
        )

    optional_features = manifest["optional_features"]
    if not isinstance(optional_features, dict):
        raise ArchiePluginError("Package manifest optional_features must be an object")
    for feature, packages in optional_features.items():
        if not isinstance(feature, str) or not feature:
            raise ArchiePluginError("Package manifest optional feature names must be non-empty")
        if not isinstance(packages, list) or any(
            not isinstance(package, str) or not package for package in packages
        ):
            raise ArchiePluginError(
                f"Package manifest optional feature {feature} must contain package names"
            )
        if len(packages) != len(set(packages)):
            raise ArchiePluginError(f"Package manifest contains duplicate values in {feature}")
        unsupported = set(packages) & official
        if unsupported:
            raise ArchiePluginError(
                f"Optional feature {feature} contains official packages: "
                + ", ".join(sorted(unsupported))
            )


def bootstrap_command(username: str, revision: str) -> str:
    args = [
        "/usr/bin/bash",
        str(BOOTSTRAP_TARGET_PATH),
        "--repository",
        ARCHIE_REPOSITORY,
        "--revision",
        revision,
        "--username",
        username,
    ]
    return shlex.join(args)


class ArchieProfile(Profile):
    def __init__(self, manifest: dict[str, Any], bootstrap_script: str, revision: str) -> None:
        super().__init__(
            "Archie",
            ProfileType.DesktopEnv,
            packages=list(manifest["official_runtime"])
            + list(manifest["build_dependencies"]),
            services=["bluetooth.service", "power-profiles-daemon.service"],
            support_gfx_driver=True,
            display_server=DisplayServerType.Wayland,
        )
        self._manifest = manifest
        self._bootstrap_script = bootstrap_script
        self._revision = revision

    @property
    def default_greeter_type(self) -> GreeterType:
        return GreeterType.Sddm

    def provision(self, install_session: Any, users: list[Any]) -> None:
        user = validate_administrative_users(users)
        info(f"Provisioning Archie for administrative user {user.username}")
        bootstrap_path = install_session.target / BOOTSTRAP_TARGET_PATH.relative_to("/")
        try:
            bootstrap_path.write_text(self._bootstrap_script, encoding="utf-8")
            bootstrap_path.chmod(0o700)
            install_session.arch_chroot(
                bootstrap_command(user.username, self._revision),
            )
        except Exception as error:
            raise ArchiePluginError(f"Archie provisioning failed: {error}") from error
        finally:
            bootstrap_path.unlink(missing_ok=True)


class Plugin:
    """Archinstall plugin entry point."""

    def __init__(self) -> None:
        from archinstall.lib.version import get_version

        current = get_version()
        validate_archinstall_version(current or "unknown")
        revision = resolve_revision(configured_repository_ref())
        manifest = load_manifest(revision)
        bootstrap_script = load_bootstrap_script(revision)
        profile_handler.add_custom_profiles(ArchieProfile(manifest, bootstrap_script, revision))
        mode = "release" if ARCHIE_RELEASE is not None else "development"
        info(f"Registered Archie desktop profile ({mode}, {revision})")
