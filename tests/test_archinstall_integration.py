import importlib.util
import json
import shlex
import subprocess
import sys
import tempfile
import types
import unittest
from enum import Enum
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = ROOT / "archinstall/plugin.py"


class FakeProfile:
    def __init__(self, name, profile_type, **kwargs):
        self.name = name
        self.profile_type = profile_type
        self.packages = kwargs.get("packages", [])
        self.services = kwargs.get("services", [])
        self._support_gfx_driver = kwargs.get("support_gfx_driver", False)
        self.display_server = kwargs.get("display_server")


class FakeProfileType(Enum):
    DesktopEnv = "Desktop Environment"


class FakeDisplayServerType(Enum):
    Wayland = "Wayland"


class FakeGreeterType(Enum):
    Sddm = "sddm"


class FakeProfileHandler:
    def __init__(self):
        self.profiles = []

    def add_custom_profiles(self, profile):
        self.profiles.extend(profile if isinstance(profile, list) else [profile])


def load_plugin():
    profile_handler = FakeProfileHandler()
    modules = {
        "archinstall.default_profiles.profile": types.SimpleNamespace(
            DisplayServerType=FakeDisplayServerType,
            GreeterType=FakeGreeterType,
            Profile=FakeProfile,
            ProfileType=FakeProfileType,
        ),
        "archinstall.lib.log": types.SimpleNamespace(info=lambda message: None),
        "archinstall.lib.profile.profiles_handler": types.SimpleNamespace(
            profile_handler=profile_handler
        ),
    }
    with patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location("archie_test_plugin", PLUGIN_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module, profile_handler


class ArchinstallPluginTest(unittest.TestCase):
    def test_manifest_has_one_source_of_package_defaults(self):
        manifest = json.loads(
            (ROOT / "archinstall/package-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema"], 1)
        self.assertTrue(
            {
                "hyprland",
                "dunst",
                "kitty",
                "uwsm",
                "dolphin",
                "wofi",
                "xdg-desktop-portal-hyprland",
                "qt5-wayland",
                "qt6-wayland",
                "polkit-kde-agent",
                "grim",
                "slurp",
            }.issubset(manifest["official_runtime"])
        )
        self.assertIn("power-profiles-daemon", manifest["official_runtime"])
        self.assertIn("yay-bin", manifest["aur_runtime"])
        self.assertEqual(manifest["optional_features"]["sddm_theme"], ["sddm-slice-qt6-git"])
        module, _ = load_plugin()
        module.validate_manifest(manifest)
        invalid = {**manifest, "aur_runtime": ["hyprland"]}
        with self.assertRaisesRegex(module.ArchiePluginError, "both official"):
            module.validate_manifest(invalid)
        invalid_feature = {**manifest, "optional_features": {"sddm_theme": ["hyprland"]}}
        with self.assertRaisesRegex(module.ArchiePluginError, "official packages"):
            module.validate_manifest(invalid_feature)

    def test_version_and_admin_validation(self):
        module, _ = load_plugin()
        module.validate_archinstall_version("4.4.3")
        with self.assertRaisesRegex(module.ArchiePluginError, "requires Archinstall"):
            module.validate_archinstall_version("4.5.0")

        admin = types.SimpleNamespace(username="archie", sudo=True)
        self.assertIs(module.validate_administrative_users([admin]), admin)
        with self.assertRaisesRegex(module.ArchiePluginError, "exactly one"):
            module.validate_administrative_users([])
        with self.assertRaisesRegex(module.ArchiePluginError, "exactly one"):
            module.validate_administrative_users([admin, admin])

    def test_development_ref_resolves_to_a_full_commit_sha(self):
        module, _ = load_plugin()
        self.assertIsNone(module.ARCHIE_RELEASE)
        self.assertEqual(module.configured_repository_ref(), "feature/archinstall-desktop")
        self.assertIn(
            "feature%2Farchinstall-desktop",
            module.repository_commits_url(module.configured_repository_ref()),
        )
        revision = "a" * 40

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps([{"id": revision}]).encode()

        with patch.object(module.urllib.request, "urlopen", return_value=FakeResponse()):
            self.assertEqual(module.resolve_revision(module.configured_repository_ref()), revision)

        with self.assertRaisesRegex(module.ArchiePluginError, "full 40-character"):
            module.validate_archie_revision("394d3cd")

    def test_profile_metadata_and_bootstrap_command(self):
        module, _ = load_plugin()
        manifest = {
            "official_runtime": ["hyprland", "stow"],
            "build_dependencies": ["git"],
        }
        revision = "b" * 40
        profile = module.ArchieProfile(manifest, "#!/bin/bash\n", revision)
        self.assertEqual(profile.name, "Archie")
        self.assertEqual(profile.profile_type, FakeProfileType.DesktopEnv)
        self.assertEqual(profile.display_server, FakeDisplayServerType.Wayland)
        self.assertEqual(profile.default_greeter_type, FakeGreeterType.Sddm)
        self.assertEqual(profile.packages, ["hyprland", "stow", "git"])

        command = module.bootstrap_command("archie", revision)
        arguments = shlex.split(command)
        self.assertEqual(arguments[0:2], ["/usr/bin/bash", "/root/archie-bootstrap.sh"])
        self.assertIn(revision, command)
        self.assertIn("--repository", arguments)
        self.assertIn("--username", arguments)
        self.assertIn("--username archie", command)
        self.assertNotIn("yay", command)
        self.assertNotIn("-c", arguments)
        self.assertNotIn(";", command)

        self.assertNotIn("--home", command)
        self.assertNotIn("--release", command)

    def test_provision_writes_and_removes_static_bootstrap(self):
        module, _ = load_plugin()

        class FakeInstallSession:
            def __init__(self, target: Path) -> None:
                self.target = target
                self.commands: list[str] = []

            def arch_chroot(self, command: str) -> None:
                self.commands.append(command)

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            (target / "root").mkdir()
            session = FakeInstallSession(target)
            profile = module.ArchieProfile(
                {"official_runtime": [], "build_dependencies": []},
                "#!/bin/bash\n",
                "c" * 40,
            )
            profile.provision(session, [types.SimpleNamespace(username="archie", sudo=True)])

            self.assertFalse((target / "root/archie-bootstrap.sh").exists())
            self.assertEqual(len(session.commands), 1)
            self.assertIn("/usr/bin/bash /root/archie-bootstrap.sh", session.commands[0])
            self.assertNotIn("/tmp/archie-bootstrap.sh", session.commands[0])

    def test_plugin_registers_archie_profile(self):
        module, profile_handler = load_plugin()
        revision = "d" * 40
        with patch.object(module, "resolve_revision", return_value=revision), patch.object(
            module,
            "load_manifest",
            return_value={
                "official_runtime": [],
                "build_dependencies": [],
            },
        ), patch.object(module, "load_bootstrap_script", return_value="#!/bin/bash\n"), patch.dict(
            sys.modules,
            {
                "archinstall.lib.version": types.SimpleNamespace(
                    get_version=lambda: "4.4.1"
                )
            },
        ):
            module.Plugin()
        self.assertEqual([profile.name for profile in profile_handler.profiles], ["Archie"])

    def test_development_validation_accepts_the_configured_repository_ref(self):
        module, _ = load_plugin()

        self.assertIsNone(module.ARCHIE_RELEASE)
        self.assertEqual(module.ARCHIE_DEVELOPMENT_REF, "feature/archinstall-desktop")

    def test_provisioner_keeps_aur_build_and_root_install_steps_separate(self):
        source = (ROOT / "archinstall/provision.sh").read_text(encoding="utf-8")
        self.assertIn("run_as_target makepkg", source)
        self.assertIn("manifest_packages aur_runtime", source)
        self.assertIn('pacman -Qpq -- "$artifact"', source)
        self.assertIn("Missing primary AUR artifact package", source)
        self.assertIn("Skipping debug AUR artifact", source)
        self.assertIn("validated_artifacts", source)
        self.assertIn('realpath -m -- "$artifact"', source)
        self.assertNotIn("pacman -Qp --print-format", source)
        self.assertIn("pacman -U --noconfirm", source)
        self.assertNotIn("makepkg --install", source)

    def test_provisioner_uses_shared_library(self):
        source = (ROOT / "archinstall/provision.sh").read_text(encoding="utf-8")

        self.assertIn('source "$SCRIPT_DIR/../lib/bash/lib.sh"', source)
        self.assertNotIn("scripts/install.sh", source)
        self.assertIn("apply_install_env_defaults", source)
        self.assertNotIn("apply_quickstart_env_defaults", source)
        self.assertIn("deploy_system_file", source)
        self.assertNotIn("deploy_copy_deployed_file_sudo", source)
        self.assertNotIn("run_sudo_cmd()", source)

    def test_provisioner_skips_debug_split_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir) / ".cache/archie/aur/archie-cli"
            primary_artifact = build_dir / "archie-cli-1-1-any.pkg.tar.zst"
            debug_artifact = build_dir / "archie-cli-debug-1-1-any.pkg.tar.zst"
            script = f"""
                set -euo pipefail
                source "$1"
                TARGET_USERNAME=archie
                TARGET_HOME={shlex.quote(temp_dir)}
                build_dir={shlex.quote(str(build_dir))}
                install_count=0
                mkdir -p "$build_dir/.git"

                run_as_target() {{
                    if [[ "$1" == git ]]; then
                        printf 'revision\\n'
                    elif [[ "$1" == makepkg && "$*" == *--packagelist* ]]; then
                        printf '%s\\n' {shlex.quote(str(primary_artifact))} {shlex.quote(str(debug_artifact))}
                    elif [[ "$1" == makepkg ]]; then
                        touch {shlex.quote(str(primary_artifact))}
                        touch {shlex.quote(str(debug_artifact))}
                    fi
                }}
                pacman() {{
                    if [[ "$3" == *archie-cli-debug* ]]; then
                        printf 'archie-cli-debug\\n'
                    else
                        printf 'archie-cli\\n'
                    fi
                }}
                run_sudo_cmd() {{
                    if [[ "$1" == pacman && "$2" == -U ]]; then
                        ((install_count += 1))
                    else
                        command "$@"
                    fi
                }}

                build_and_install_aur_package archie-cli
                [[ "$install_count" == 1 ]]
            """
            result = subprocess.run(
                ["bash", "-c", script, "bash", str(ROOT / "archinstall/provision.sh")],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Skipping debug AUR artifact", result.stderr)

    def test_provisioner_deploys_makepkg_config_before_aur_builds(self):
        config = ROOT / "deployment-packages/etc/makepkg.conf.d/archie.conf"
        self.assertEqual(config.read_text(encoding="utf-8"), "# Do not generate separate debug symbol packages during Archie provisioning.\nOPTIONS+=('!debug')\n")

        source = (ROOT / "archinstall/provision.sh").read_text(encoding="utf-8")
        main_source = source[source.index("main()") :]
        self.assertLess(
            main_source.index("deploy_system_packages"),
            main_source.index("install_aur_packages"),
        )

    def test_provisioner_rejects_artifacts_outside_build_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir) / ".cache/archie/aur/archie-cli"
            outside_artifact = Path(temp_dir) / ".cache/archie/aur/outside/archie-cli-1-1-any.pkg.tar.zst"
            script = f"""
                set -euo pipefail
                source "$1"
                TARGET_USERNAME=archie
                TARGET_HOME={shlex.quote(temp_dir)}
                build_dir={shlex.quote(str(build_dir))}
                mkdir -p "$build_dir/.git" "$(dirname {shlex.quote(str(outside_artifact))})"
                touch {shlex.quote(str(outside_artifact))}

                run_as_target() {{
                    if [[ "$1" == git ]]; then
                        printf 'revision\\n'
                    elif [[ "$1" == makepkg && "$*" == *--packagelist* ]]; then
                        printf '%s\\n' {shlex.quote(str(outside_artifact))}
                    fi
                }}

                build_and_install_aur_package archie-cli
            """
            result = subprocess.run(
                ["bash", "-c", script, "bash", str(ROOT / "archinstall/provision.sh")],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("AUR artifact escaped its build directory", result.stderr)

    def test_provisioner_owns_each_user_cache_directory(self):
        source = (ROOT / "archinstall/provision.sh").read_text(encoding="utf-8")
        ownership_flags = '-m 0755 -o "$TARGET_UID" -g "$TARGET_GID"'
        self.assertIn(f'{ownership_flags} "$TARGET_HOME/.config"', source)
        self.assertIn(f'{ownership_flags} "$TARGET_HOME/.local"', source)
        self.assertIn(f'{ownership_flags} "$TARGET_HOME/.cache"', source)
        self.assertIn(f'{ownership_flags} "$TARGET_HOME/.cache/archie"', source)
        self.assertIn(f'{ownership_flags} "$TARGET_HOME/.cache/archie/aur"', source)

    def test_provisioner_assumes_a_fresh_target_without_backups(self):
        source = (ROOT / "archinstall/provision.sh").read_text(encoding="utf-8")
        self.assertIn("mapfile -t aur_packages < <(manifest_packages aur_runtime)", source)
        self.assertNotIn("backup_system_targets", source)
        self.assertNotIn("backup_stow_conflicts", source)
        self.assertNotIn("backup_copy_deployed", source)
        self.assertNotIn("archie-pre-stow-backup", source)

    def test_bootstrap_is_a_static_bash_boundary(self):
        bootstrap = ROOT / "archinstall/bootstrap.sh"
        source = bootstrap.read_text(encoding="utf-8")
        subprocess.run(["bash", "-n", str(bootstrap)], check=True)
        self.assertTrue(source.startswith("#!/bin/bash\n\nset -euo pipefail\n"))
        self.assertIn("git -C \"$checkout\" fetch --depth=1 origin \"$revision\"", source)
        self.assertIn('bash "$checkout/archinstall/provision.sh"', source)
        self.assertNotIn("--release", source)
        self.assertNotIn("--home", source)


if __name__ == "__main__":
    unittest.main()
