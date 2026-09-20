import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "lib/bash/lib.sh"
INSTALLER = ROOT / "scripts/install.sh"
MANIFEST = ROOT / "archinstall/package-manifest.json"


def run_bash(script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", script, "bash", str(LIBRARY), *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


class ShellLibraryTest(unittest.TestCase):
    def test_quickstart_bool_enabled_accepts_documented_truthy_values(self):
        for value in ("1", "true", "TRUE", "yes", "on"):
            with self.subTest(value=value):
                run_bash('source "$1"; quickstart_bool_enabled "$2"', value)

    def test_quickstart_bool_enabled_rejects_other_values(self):
        for value in ("0", "false", "no", "off", "", "unexpected"):
            with self.subTest(value=value):
                result = subprocess.run(
                    [
                        "bash",
                        "-c",
                        'source "$1"; quickstart_bool_enabled "$2"',
                        "bash",
                        str(LIBRARY),
                        value,
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 1)

    def test_manifest_packages_reads_required_aur_packages(self):
        result = run_bash('source "$1"; manifest_packages aur_runtime')

        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(result.stdout.splitlines(), manifest["aur_runtime"])

    def test_manifest_optional_packages_reads_feature_packages(self):
        result = run_bash('source "$1"; manifest_optional_packages sddm_theme')

        self.assertEqual(result.stdout.splitlines(), ["sddm-slice-qt6-git"])

    def test_run_cmd_preserves_arguments_and_logs_the_command(self):
        result = run_bash(
            'source "$1"; run_cmd printf "%s|%s\\n" "two words" \'literal$sign\''
        )

        self.assertIn("+ printf", result.stdout)
        self.assertTrue(result.stdout.endswith("two words|literal$sign\n"))

    def test_stow_wrappers_use_supported_long_option_syntax(self):
        result = subprocess.run(
            [
                "bash",
                "-c",
                (
                    "source \"$1\"; "
                    "run_cmd() { printf 'user:%s\\n' \"$*\"; }; "
                    "run_sudo_cmd() { printf 'sudo:%s\\n' \"$*\"; }; "
                    "stow_package \"/home/test\" home; "
                    "stow_package_sudo /etc etc"
                ),
                "bash",
                str(INSTALLER),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            result.stdout.splitlines(),
            [
                f"user:stow --dir={ROOT / 'deployment-packages'} --target=/home/test home",
                f"sudo:stow --dir={ROOT / 'deployment-packages'} --target=/etc etc",
            ],
        )
