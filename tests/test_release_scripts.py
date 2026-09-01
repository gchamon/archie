import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "scripts/release/prepare-archie-cli-aur.sh"
VERIFY = ROOT / "scripts/release/verify-archie-cli-package.sh"


class ArchieCliReleaseVersionTest(unittest.TestCase):
    def run_prepare(self, package_dir: Path, channel: str, commit: str, package_release: str | None = None) -> None:
        env = os.environ | {
            "ARCHIE_CLI_AUR_DIR": str(package_dir),
            "ARCHIE_CLI_CHANNEL": channel,
        }
        if package_release is not None:
            env["ARCHIE_CLI_PACKAGE_RELEASE"] = package_release
        subprocess.run([str(PREPARE), commit], cwd=ROOT, env=env, check=True)

    def run_verify(self, package_dir: Path, channel: str, package_release: str | None = None) -> None:
        env = os.environ | {
            "ARCHIE_CLI_AUR_DIR": str(package_dir),
            "ARCHIE_CLI_CHANNEL": channel,
        }
        if package_release is not None:
            env["ARCHIE_CLI_PACKAGE_RELEASE"] = package_release
        subprocess.run([str(VERIFY)], cwd=ROOT, env=env, check=True)

    def test_alpha_and_rc_versions_use_pipeline_release_numbers(self) -> None:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        with tempfile.TemporaryDirectory() as temporary:
            package_dir = Path(temporary) / "archie-cli-nightly"
            package_dir.mkdir()
            subprocess.run(["git", "init", "--initial-branch=master", str(package_dir)], check=True, capture_output=True)

            self.run_prepare(package_dir, "alpha", commit, "283")
            alpha_pkgbuild = (package_dir / "PKGBUILD").read_text()
            self.assertIn("pkgver=0.2.0a", alpha_pkgbuild)
            self.assertIn("pkgrel=283", alpha_pkgbuild)
            self.assertIn(f"_commit={commit}", alpha_pkgbuild)
            self.run_verify(package_dir, "alpha", "283")

            self.run_prepare(package_dir, "rc", commit, "284")
            rc_pkgbuild = (package_dir / "PKGBUILD").read_text()
            self.assertIn("pkgver=0.2.0rc", rc_pkgbuild)
            self.assertIn("pkgrel=284", rc_pkgbuild)
            self.run_verify(package_dir, "rc", "284")

    def test_stable_verification_ignores_prerelease_pipeline_release_number(self) -> None:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        with tempfile.TemporaryDirectory() as temporary:
            package_dir = Path(temporary) / "archie-cli"
            package_dir.mkdir()
            subprocess.run(["git", "init", "--initial-branch=master", str(package_dir)], check=True, capture_output=True)

            self.run_prepare(package_dir, "stable", commit, "283")
            stable_pkgbuild = (package_dir / "PKGBUILD").read_text()
            self.assertIn("pkgver=0.2.0", stable_pkgbuild)
            self.assertIn("pkgrel=1", stable_pkgbuild)
            self.run_verify(package_dir, "stable", "283")

    def test_repeating_the_same_commit_keeps_package_release_idempotent(self) -> None:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        with tempfile.TemporaryDirectory() as temporary:
            package_dir = Path(temporary) / "archie-cli-nightly"
            package_dir.mkdir()
            subprocess.run(["git", "init", "--initial-branch=master", str(package_dir)], check=True, capture_output=True)

            self.run_prepare(package_dir, "alpha", commit)
            first_release = next(
                line.removeprefix("pkgrel=")
                for line in (package_dir / "PKGBUILD").read_text().splitlines()
                if line.startswith("pkgrel=")
            )
            self.run_prepare(package_dir, "alpha", commit)
            second_release = next(
                line.removeprefix("pkgrel=")
                for line in (package_dir / "PKGBUILD").read_text().splitlines()
                if line.startswith("pkgrel=")
            )
            self.assertEqual(first_release, second_release)
