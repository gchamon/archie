import os
import subprocess
import tempfile
import unittest
from pathlib import Path

MIC_INDICATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "deployment-packages/config/hypr/scripts/waybar-mic-indicator.sh"
)


class MicrophoneIndicatorTest(unittest.TestCase):
    def run_indicator(self, *, source_outputs: str, source_muted: bool) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_path = Path(temp_dir)
            pactl_path = temporary_path / "pactl"
            pactl_path.write_text(
                """#!/bin/bash
case "$*" in
    "list source-outputs short") printf '%s\\n' "$PACTL_SOURCE_OUTPUTS" ;;
    "get-default-source") printf 'default-microphone\\n' ;;
    "get-source-mute default-microphone") printf 'Mute: %s\\n' "$PACTL_SOURCE_MUTED" ;;
esac
""",
                encoding="utf-8",
            )
            pactl_path.chmod(0o755)
            environment = os.environ | {
                "PATH": f"{temporary_path}:{os.environ['PATH']}",
                "PACTL_SOURCE_OUTPUTS": source_outputs,
                "PACTL_SOURCE_MUTED": "yes" if source_muted else "no",
            }
            return subprocess.run(
                [MIC_INDICATOR_PATH],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )

    def test_emits_mic_for_active_unmuted_capture(self) -> None:
        result = self.run_indicator(source_outputs="42\t...", source_muted=False)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "MIC\n")

    def test_hides_mic_without_capture(self) -> None:
        result = self.run_indicator(source_outputs="", source_muted=False)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_hides_mic_when_default_source_is_muted(self) -> None:
        result = self.run_indicator(source_outputs="42\t...", source_muted=True)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_emits_nothing_when_pactl_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [MIC_INDICATOR_PATH],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ | {"PATH": temp_dir},
            )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


class ManagedWaybarThemesTest(unittest.TestCase):
    def test_every_theme_declares_and_styles_the_mic_indicator(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for theme_root in (
            root / "deployment-packages/config/waybar/themes",
            root / "src/archie/waybar-themes",
        ):
            for theme in ("cjbassi", "mechabar", "tokyonight"):
                with self.subTest(theme_root=theme_root, theme=theme):
                    config = (theme_root / theme / "config").read_text(encoding="utf-8")
                    style = (theme_root / theme / "style.css").read_text(encoding="utf-8")

                    self.assertIn('"custom/mic"', config)
                    self.assertIn("waybar-mic-indicator.sh", config)
                    self.assertIn("#custom-mic", style)
