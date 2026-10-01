import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

MIC_INDICATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "deployment-packages/config/hypr/scripts/waybar-mic-indicator.sh"
)

MEMORY_INDICATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "deployment-packages/config/hypr/scripts/waybar-memory-indicator.sh"
)

SOUND_INDICATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "deployment-packages/config/hypr/scripts/waybar-sound-indicator.sh"
)
BATTERY_INDICATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "deployment-packages/config/hypr/scripts/waybar-battery-indicator.sh"
)


class SoundIndicatorTest(unittest.TestCase):
    sinks = """Sink #1
    Name: speaker
    Description: Internal Speakers
    Mute: no
    Volume: front-left: 42595 / 65% / -11.23 dB, front-right: 42595 / 65%
"""
    sources = """Source #1
    Name: microphone
    Description: Built-in Microphone
    Mute: no
    Volume: front-left: 61680 / 94% / -1.58 dB
Source #2
    Name: usb-webcam
    Description: HD Webcam Microphone
    Mute: yes
    Volume: front-left: 30000 / 45% / -6.00 dB
Source #3
    Name: speaker.monitor
    Description: Webcam monitor
    Mute: no
    Volume: front-left: 30000 / 45% / -6.00 dB
"""

    def run_indicator(
        self,
        *,
        sink: str = "speaker",
        source: str = "microphone",
        fail: str = "",
        sink_description: str = "Internal Speakers",
        source_description: str = "Built-in Microphone",
        webcam_description: str = "HD Webcam Microphone",
        sink_muted: bool = False,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_path = Path(temp_dir)
            sink_file = temporary_path / "sinks"
            source_file = temporary_path / "sources"
            sink_contents = self.sinks
            if sink != "missing":
                sink_contents = sink_contents.replace("Name: speaker", f"Name: {sink}")
            sink_contents = sink_contents.replace("Internal Speakers", sink_description)
            if sink_muted:
                sink_contents = sink_contents.replace("Mute: no", "Mute: yes")
            sink_file.write_text(sink_contents, encoding="utf-8")
            source_file.write_text(
                self.sources.replace("Built-in Microphone", source_description).replace(
                    "HD Webcam Microphone", webcam_description
                ),
                encoding="utf-8",
            )
            pactl_path = temporary_path / "pactl-fixture"
            pactl_path.write_text(
                """#!/bin/bash
if [[ "$*" == "$PACTL_FAIL" ]]; then exit 1; fi
case "$*" in
    "get-default-sink") printf '%s\\n' "$DEFAULT_SINK" ;;
    "get-default-source") printf '%s\\n' "$DEFAULT_SOURCE" ;;
    "list sinks") cat "$SINKS_FILE" ;;
    "list sources") cat "$SOURCES_FILE" ;;
esac
""",
                encoding="utf-8",
            )
            pactl_path.chmod(0o755)
            return subprocess.run(
                [SOUND_INDICATOR_PATH],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ | {
                    "PACTL_COMMAND": str(pactl_path),
                    "DEFAULT_SINK": sink,
                    "DEFAULT_SOURCE": source,
                    "SINKS_FILE": str(sink_file),
                    "SOURCES_FILE": str(source_file),
                    "PACTL_FAIL": fail,
                },
            )

    def test_shows_bluetooth_icon_for_default_bluetooth_sink(self) -> None:
        bluetooth_sink = "bluez_output.00_11_22_33_44_55.1"

        connected = self.run_indicator(sink=bluetooth_sink)
        self.assertEqual(connected.returncode, 0, connected.stderr)
        self.assertEqual(json.loads(connected.stdout)["text"], " 65% ")

        muted = self.run_indicator(sink=bluetooth_sink, sink_muted=True)
        self.assertEqual(muted.returncode, 0, muted.stderr)
        self.assertEqual(json.loads(muted.stdout)["text"], "󰝟 Mute ")

        ordinary = self.run_indicator(sink="speaker")
        self.assertEqual(ordinary.returncode, 0, ordinary.stderr)
        text = json.loads(ordinary.stdout)["text"]
        self.assertEqual(text, " 65%")
        self.assertNotIn("", text)

    def test_reports_default_routes_and_detects_webcam_input(self) -> None:
        result = self.run_indicator()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["text"], " 65%")
        self.assertIn(
            f"{'Output:':<10} {'Internal Speakers':<25} 65% (unmuted)",
            data["tooltip"],
        )
        self.assertIn(
            f"{'Input:':<10} {'Built-in Microphone':<25} 94% (unmuted)",
            data["tooltip"],
        )
        self.assertIn(
            f"{'Webcam:':<10} {'HD Webcam Microphone':<25} 45% (muted)",
            data["tooltip"],
        )
        tooltip_rows = data["tooltip"].splitlines()
        output_row = next(row for row in tooltip_rows if row.startswith("Output:"))
        input_row = next(row for row in tooltip_rows if row.startswith("Input:"))
        webcam_row = next(row for row in tooltip_rows if row.startswith("Webcam:"))
        self.assertEqual(output_row.index("65%"), input_row.index("94%"))
        self.assertEqual(output_row.index("65%"), webcam_row.index("45%"))
        self.assertNotIn("Webcam monitor", data["tooltip"])

    def test_middle_truncates_long_audio_device_descriptions(self) -> None:
        result = self.run_indicator(
            sink_description="SINKPREFIX12-middle-to-truncate-SINKSUFFIX12",
            source_description="INPUTPREFIX1-middle-to-truncate-INPUTSUFFIX1",
            webcam_description="WEBCAMPREFIX-middle-to-truncate-WEBCAMSUFFIX",
        )
        tooltip = json.loads(result.stdout)["tooltip"]

        self.assertIn(
            f"{'Output:':<10} {'SINKPREFIX12…SINKSUFFIX12':<25} 65% (unmuted)",
            tooltip,
        )
        self.assertIn(
            f"{'Input:':<10} {'INPUTPREFIX1…INPUTSUFFIX1':<25} 94% (unmuted)",
            tooltip,
        )
        self.assertIn(
            f"{'Webcam:':<10} {'WEBCAMPREFIX…WEBCAMSUFFIX':<25} 45% (muted)",
            tooltip,
        )

        within_limit = "1234567890123456789012345"
        within_limit_result = self.run_indicator(sink_description=within_limit)
        self.assertIn(
            f"{'Output:':<10} {within_limit:<25} 65% (unmuted)",
            json.loads(within_limit_result.stdout)["tooltip"],
        )

    def test_muted_output_and_invalid_default_devices(self) -> None:
        muted = self.run_indicator(sink="missing")
        self.assertNotEqual(muted.returncode, 0)
        self.assertEqual(muted.stdout, "")

        invalid_source = self.run_indicator(source="missing")
        self.assertNotEqual(invalid_source.returncode, 0)
        self.assertEqual(invalid_source.stdout, "")

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "pactl"
            path.write_text(
                """#!/bin/bash
case "$*" in
    "get-default-sink") echo speaker ;;
    "get-default-source") echo microphone ;;
    "list sinks") sed 's/Mute: no/Mute: yes/' "$SINKS_FILE" ;;
    "list sources") cat "$SOURCES_FILE" ;;
esac
""",
                encoding="utf-8",
            )
            path.chmod(0o755)
            sink_path = Path(temp_dir) / "sinks"
            source_path = Path(temp_dir) / "sources"
            sink_path.write_text(self.sinks, encoding="utf-8")
            source_path.write_text(self.sources, encoding="utf-8")
            result = subprocess.run(
                [SOUND_INDICATOR_PATH],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ | {
                    "PACTL_COMMAND": str(path),
                    "SINKS_FILE": str(sink_path),
                    "SOURCES_FILE": str(source_path),
                },
            )
            self.assertEqual(json.loads(result.stdout)["text"], "󰝟 Mute")


class BatteryIndicatorTest(unittest.TestCase):
    battery = """  state: discharging
  time to empty: 2.5 hours
  percentage: 42%
  capacity: 91.5%
  charge-cycles: 120
"""

    def run_indicator(
        self,
        *,
        battery: str | None = None,
        battery_path: str = "/org/freedesktop/UPower/devices/battery_BAT0",
        line_power_path: str = "/org/freedesktop/UPower/devices/line_power_AC",
        line_power_info: str = "  online: no\n",
        fail: str = "",
        uptime_text: str = "up 2 hours",
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_path = Path(temp_dir)
            info_file = temporary_path / "battery-info"
            info_file.write_text(self.battery if battery is None else battery, encoding="utf-8")
            line_power_file = temporary_path / "line-power-info"
            line_power_file.write_text(line_power_info, encoding="utf-8")
            upower_path = temporary_path / "upower-fixture"
            upower_path.write_text(
                """#!/bin/bash
if [[ "$*" == "$UPOWER_FAIL" ]]; then exit 1; fi
if [[ "$1" == -e ]]; then
    printf '%s\\n' "$BATTERY_PATH" "$LINE_POWER_PATH"
elif [[ "$2" == "$BATTERY_PATH" ]]; then
    cat "$BATTERY_INFO"
else
    cat "$LINE_POWER_INFO"
fi
""",
                encoding="utf-8",
            )
            upower_path.chmod(0o755)
            uptime_path = temporary_path / "uptime-fixture"
            uptime_path.write_text(
                """#!/bin/bash
printf '%s\\n' "$UPTIME_TEXT"
""",
                encoding="utf-8",
            )
            uptime_path.chmod(0o755)
            who_path = temporary_path / "who-fixture"
            who_path.write_text(
                """#!/bin/bash
printf '  system boot  2026-09-28 00:02\\n'
""",
                encoding="utf-8",
            )
            who_path.chmod(0o755)
            return subprocess.run(
                [BATTERY_INDICATOR_PATH],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ | {
                    "UPOWER_COMMAND": str(upower_path),
                    "UPTIME_COMMAND": str(uptime_path),
                    "WHO_COMMAND": str(who_path),
                    "BATTERY_PATH": battery_path,
                    "BATTERY_INFO": str(info_file),
                    "LINE_POWER_PATH": line_power_path,
                    "LINE_POWER_INFO": str(line_power_file),
                    "UPOWER_FAIL": fail,
                    "UPTIME_TEXT": uptime_text,
                },
            )

    def test_reports_native_battery_metrics_and_low_state_class(self) -> None:
        result = self.run_indicator()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["text"], " 42%")
        self.assertEqual(data["class"], "battery")
        self.assertIn(f"{'Estimated runtime:':<20} 2.5 hours", data["tooltip"])
        self.assertIn(f"{'Health:':<20} 91.5%", data["tooltip"])
        self.assertIn(f"{'Charge cycles:':<20} 120", data["tooltip"])
        self.assertIn(f"{'Uptime:':<20} 2 hours", data["tooltip"])
        self.assertNotIn("TTF", data["tooltip"])
        self.assertIn(
            f"{'Last reboot:':<20} 2026-09-28 00:02 (0 days ago)",
            data["tooltip"],
        )

    def test_reports_rounded_reboot_age_in_days(self) -> None:
        for uptime_text, reboot_age in (
            ("up 1 day, 3 hours", "1 day ago"),
            ("up 1 day, 12 hours", "2 days ago"),
            ("up 1 week, 4 days", "11 days ago"),
        ):
            with self.subTest(uptime_text=uptime_text):
                result = self.run_indicator(uptime_text=uptime_text)
                data = json.loads(result.stdout)
                self.assertIn(
                    f"{'Uptime:':<20} {uptime_text.removeprefix('up ')}",
                    data["tooltip"],
                )
                self.assertIn(
                    f"{'Last reboot:':<20} 2026-09-28 00:02 ({reboot_age})",
                    data["tooltip"],
                )

    def test_uses_native_icon_and_class_thresholds(self) -> None:
        for percentage, expected_icon, expected_class in (
            (10, "", "critical"),
            (20, "", "warning"),
            (35, "", "battery"),
            (65, "", "battery"),
            (85, "", "battery"),
        ):
            with self.subTest(percentage=percentage):
                info = (
                    f"  state: discharging\n"
                    f"  percentage: {percentage}%\n"
                )
                result = self.run_indicator(battery=info)
                data = json.loads(result.stdout)
                self.assertEqual(data["text"], f"{expected_icon} {percentage}%")
                self.assertEqual(data["class"], expected_class)

    def test_charging_uses_a_charging_icon_without_changing_severity(self) -> None:
        for percentage, expected_class in (
            (10, "critical"),
            (42, "battery"),
            (85, "battery"),
        ):
            with self.subTest(percentage=percentage):
                info = f"  state: charging\n  percentage: {percentage}%\n"
                result = self.run_indicator(battery=info)
                data = json.loads(result.stdout)

                self.assertEqual(data["text"], f"󰂄 {percentage}%")
                self.assertEqual(data["class"], expected_class)
                self.assertIn(
                    f"{'Charge:':<20} {percentage}% (charging; TTF: unavailable)",
                    data["tooltip"],
                )
        full = self.run_indicator(
            battery="  state: fully-charged\n  percentage: 100%\n"
        )
        self.assertEqual(json.loads(full.stdout)["text"], " 100%")

    def test_shows_upower_time_to_full_next_to_charging_label(self) -> None:
        info = (
            "  state: charging\n"
            "  time to full: 1.25 hours\n"
            "  time to empty: unavailable\n"
            "  percentage: 42%\n"
        )

        result = self.run_indicator(battery=info)
        data = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            data["tooltip"].splitlines()[1],
            f"{'Charge:':<20} 42% (charging; TTF: 1.25 hours)",
        )

    def test_uses_dash_for_runtime_when_power_adapter_is_online(self) -> None:
        result = self.run_indicator(
            battery="  state: fully-charged\n  percentage: 100%\n",
            line_power_info="  online: yes\n",
        )
        data = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"{'Estimated runtime:':<20} —", data["tooltip"])


    def test_uses_health_and_runtime_fallbacks_and_rejects_missing_battery(self) -> None:
        optional_missing = self.run_indicator(
            battery="  state: fully-charged\n  percentage: 100%\n"
        )
        data = json.loads(optional_missing.stdout)
        self.assertEqual(data["class"], "battery")
        self.assertIn(f"{'Estimated runtime:':<20} unavailable", data["tooltip"])
        self.assertIn(f"{'Health:':<20} unavailable", data["tooltip"])
        self.assertIn(f"{'Charge cycles:':<20} unavailable", data["tooltip"])
        absent = self.run_indicator(battery_path="")
        self.assertNotEqual(absent.returncode, 0)
        self.assertEqual(absent.stdout, "")

        info_failure = self.run_indicator(fail="-i /org/freedesktop/UPower/devices/battery_BAT0")
        self.assertNotEqual(info_failure.returncode, 0)
        self.assertEqual(info_failure.stdout, "")

        for failure in ("-e",):
            failed = self.run_indicator(fail=failure)
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(failed.stdout, "")


class MemoryIndicatorTest(unittest.TestCase):
    def run_indicator(self, *, meminfo: str, processes: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_path = Path(temp_dir)
            meminfo_path = temporary_path / "meminfo"
            meminfo_path.write_text(meminfo, encoding="utf-8")
            ps_path = temporary_path / "ps"
            ps_path.write_text(
                "#!/bin/bash\nprintf '%s\\n' \"$PS_OUTPUT\"\n",
                encoding="utf-8",
            )
            ps_path.chmod(0o755)
            environment = os.environ | {
                "MEMINFO_PATH": str(meminfo_path),
                "PATH": f"{temporary_path}:{os.environ['PATH']}",
                "PS_OUTPUT": processes,
            }
            return subprocess.run(
                [MEMORY_INDICATOR_PATH],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )

    def test_summarizes_five_largest_process_groups(self) -> None:
        result = self.run_indicator(
            meminfo="MemTotal: 16777216 kB\nMemAvailable: 8388608 kB\n",
            processes=(
                "2048 Web Content\n"
                "2048 editor\n"
                "1536 compositor\n"
                "1024 daemon\n"
                "768 terminal\n"
                "1024 Web Content\n"
                "512 helper\n"
            ),
        )

        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data["text"], "50%")
        tooltip_lines = data["tooltip"].splitlines()
        self.assertEqual(
            tooltip_lines[:2],
            ["8.0/16.0 GiB", "Top memory consumers"],
        )
        rows = tooltip_lines[2:]
        self.assertEqual(
            [row[:12].rstrip() for row in rows],
            ["Web Content", "editor", "compositor", "daemon", "terminal"],
        )
        self.assertEqual(
            [row[12:].strip() for row in rows],
            ["3.0 MiB", "2.0 MiB", "1.5 MiB", "1.0 MiB", "0.8 MiB"],
        )
        self.assertEqual(len({row.index("MiB") for row in rows}), 1)
        self.assertEqual(data["class"], "memory")

    def test_reports_empty_process_list(self) -> None:
        result = self.run_indicator(
            meminfo="MemTotal: 16777216 kB\nMemAvailable: 8388608 kB\n",
            processes="",
        )

        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data["text"], "50%")
        self.assertEqual(
            data["tooltip"],
            "8.0/16.0 GiB\n"
            "Top memory consumers\n"
            "No processes found",
        )
        self.assertEqual(data["class"], "memory")

    def test_rejects_missing_or_zero_total_memory(self) -> None:
        for meminfo in (
            "MemAvailable: 4096 kB\n",
            "MemTotal: 0 kB\nMemAvailable: 0 kB\n",
        ):
            with self.subTest(meminfo=meminfo):
                result = self.run_indicator(meminfo=meminfo, processes="1024 browser")

                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")



class DiskIndicatorTest(unittest.TestCase):
    fixture = (
        "Type Size Used Use% Mounted on\n"
        "ext4 468G 134G 31% /\n"
        "vfat 1022M 66M 7% /boot\n"
        "btrfs 2T 1T 50% /mnt/mapper\n"
        "nfs4 7.3T 2.3T 33% /media/storage\n"
        "tmpfs 8G 0 0% /run\n"
        "devtmpfs 8G 0 0% /dev\n"
        "efivarfs 128K 20K 16% /sys/firmware/efi/efivars\n"
    )

    def run_indicator(self, output: str, *, fail: bool = False) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_path = Path(temp_dir)
            fixture_path = temporary_path / "df-output"
            fixture_path.write_text(output, encoding="utf-8")
            command_path = temporary_path / "df-fixture"
            command_path.write_text(
                "#!/bin/bash\n"
                "if [[ \"${DF_FAIL:-}\" == 1 ]]; then exit 1; fi\n"
                "awk 'NR == 1 || ($1 != \"tmpfs\" && $1 != \"devtmpfs\" && $1 != \"efivarfs\")' \"$DF_FIXTURE\"\n",
                encoding="utf-8",
            )
            command_path.chmod(0o755)
            return subprocess.run(
                [DISK_INDICATOR_PATH],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ | {
                    "DF_COMMAND": str(command_path),
                    "DF_FIXTURE": str(fixture_path),
                    "DF_FAIL": "1" if fail else "",
                },
            )

    def test_reports_filtered_mounts_with_aligned_columns(self) -> None:
        result = self.run_indicator(self.fixture)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["text"], "31%")
        rows = data["tooltip"].splitlines()
        self.assertEqual(rows[0], "Disk usage")
        self.assertEqual(len(rows), 5)
        self.assertEqual([row.split()[0] for row in rows[1:]], ["/", "/boot", "/mnt/mapper", "/media/storage"])
        capacity_ends = {
            row.index("  ", row.index(" / ") + 3)
            for row in rows[1:]
        }
        self.assertEqual(len(capacity_ends), 1)
        self.assertNotIn("/run", data["tooltip"])
        self.assertNotIn("/dev", data["tooltip"])
        self.assertNotIn("/sys/firmware", data["tooltip"])
        self.assertEqual(len({row.rfind("%") for row in rows[1:]}), 1)

    def test_supports_root_only_and_rejects_invalid_input(self) -> None:
        root_only = self.run_indicator("Type Size Used Use% Mounted on\next4 468G 134G 31% /\n")
        self.assertEqual(root_only.returncode, 0, root_only.stderr)
        self.assertEqual(json.loads(root_only.stdout)["tooltip"], "Disk usage\n/  134G / 468G  31%")

        for output, fail in ((self.fixture, True), ("Type Size Used Use% Mounted on\next4 468G 134G 31% /home\n", False)):
            with self.subTest(fail=fail, output=output):
                result = self.run_indicator(output, fail=fail)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")


DISK_INDICATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "deployment-packages/config/hypr/scripts/waybar-disk-indicator.sh"
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
    def test_waybar_launcher_watches_the_replaced_style_path(self) -> None:
        root = Path(__file__).resolve().parents[1]
        launcher = (
            root / "deployment-packages/config/hypr/scripts/launch-waybar.sh"
        ).read_text(encoding="utf-8")

        self.assertIn("--event moved_to", launcher)
        self.assertIn("--include '.*/style\\.css$'", launcher)
        self.assertNotIn("killall waybar", launcher)

    def test_every_theme_shows_workspace_names_only_by_default(self) -> None:
        root = Path(__file__).resolve().parents[1]
        theme_root = root / "src/archie/waybar-themes"

        for theme in ("cjbassi", "mechabar", "tokyonight"):
            with self.subTest(theme=theme):
                config = json.loads(
                    (theme_root / theme / "config")
                    .read_text(encoding="utf-8")
                    .split("\n", 1)[1]
                )
                workspace = config["hyprland/workspaces"]

                self.assertTrue(workspace["disable-scroll"])
                self.assertEqual(workspace["format"], "{name}")
                self.assertNotIn("windows", workspace["format"])
                self.assertNotIn("format-window-separator", workspace)
                self.assertNotIn("window-rewrite", workspace)
                self.assertNotIn("window-rewrite-default", workspace)

    def test_theme_styles_do_not_reset_native_menu_controls(self) -> None:
        root = Path(__file__).resolve().parents[1]
        package_root = root / "src/archie/waybar-themes"

        for theme in ("cjbassi", "mechabar", "tokyonight"):
            with self.subTest(theme=theme):
                style = (package_root / theme / "style.css").read_text(
                    encoding="utf-8"
                )

                self.assertNotIn("\n* {", f"\n{style}")
                self.assertNotIn("window#waybar *", style)
                self.assertNotIn("menu *", style)

    def test_mechabar_preserves_its_module_spacing(self) -> None:
        root = Path(__file__).resolve().parents[1]
        style = (root / "src/archie/waybar-themes/mechabar/style.css").read_text(
            encoding="utf-8"
        )

        self.assertIn("padding: 0 10px;", style)
        self.assertIn("margin: 4px 2px;", style)
        self.assertIn("border-radius: 8px;", style)

    def test_every_theme_declares_and_styles_the_mic_indicator(self) -> None:
        root = Path(__file__).resolve().parents[1]
        theme_root = root / "src/archie/waybar-themes"
        for theme in ("cjbassi", "mechabar", "tokyonight"):
            with self.subTest(theme=theme):
                config = (theme_root / theme / "config").read_text(encoding="utf-8")
                style = (theme_root / theme / "style.css").read_text(encoding="utf-8")

                self.assertIn('"custom/mic"', config)
                self.assertIn("waybar-mic-indicator.sh", config)
                self.assertIn("#custom-mic", style)

    def test_every_theme_uses_the_top_memory_tooltip(self) -> None:
        root = Path(__file__).resolve().parents[1]
        theme_root = root / "src/archie/waybar-themes"

        for theme in ("cjbassi", "mechabar", "tokyonight"):
            with self.subTest(theme=theme):
                config = (theme_root / theme / "config").read_text(encoding="utf-8")
                style = (theme_root / theme / "style.css").read_text(encoding="utf-8")

                self.assertIn('"custom/memory"', config)
                self.assertNotIn('"memory"', config)
                self.assertIn("waybar-memory-indicator.sh", config)
                self.assertIn('"format": " {text}"', config)
                self.assertIn('"return-type": "json"', config)
                self.assertIn(
                    '"on-click": "gnome-system-monitor --show-processes-tab"',
                    config,
                )
                self.assertIn("#custom-memory", style)
                self.assertNotIn("#memory", style)

    def test_every_theme_uses_the_disk_usage_tooltip(self) -> None:
        root = Path(__file__).resolve().parents[1]
        theme_root = root / "src/archie/waybar-themes"

        for theme in ("cjbassi", "mechabar", "tokyonight"):
            with self.subTest(theme=theme):
                config = (theme_root / theme / "config").read_text(encoding="utf-8")
                style = (theme_root / theme / "style.css").read_text(encoding="utf-8")

                self.assertIn('"custom/disk"', config)
                self.assertNotIn('"disk"', config)
                self.assertIn("waybar-disk-indicator.sh", config)
                self.assertIn('"format": "󱛟 {text}"', config)
                self.assertIn('"return-type": "json"', config)
                self.assertIn('"on-click": "kitty ncdu ~"', config)
                self.assertIn(
                    '"on-click-right": "gnome-system-monitor --show-file-systems-tab"',
                    config,
                )
                self.assertIn("#custom-disk", style)
                self.assertNotIn("#disk", style)

    def test_every_theme_uses_custom_sound_and_battery_indicators(self) -> None:
        root = Path(__file__).resolve().parents[1]
        theme_root = root / "src/archie/waybar-themes"

        for theme in ("cjbassi", "mechabar", "tokyonight"):
            with self.subTest(theme=theme):
                config = (theme_root / theme / "config").read_text(encoding="utf-8")
                style = (theme_root / theme / "style.css").read_text(encoding="utf-8")
                self.assertIn('"custom/sound"', config)
                self.assertIn('"custom/battery"', config)
                self.assertNotIn('"pulseaudio"', config)
                self.assertNotIn('"battery"', config)
                self.assertIn("waybar-sound-indicator.sh", config)
                self.assertIn("waybar-battery-indicator.sh", config)
                self.assertIn('"return-type": "json"', config)
                self.assertIn('"on-click": "pavucontrol"', config)
                self.assertIn('"on-click-right": "pamixer -t"', config)
                self.assertIn('"on-scroll-up": "pamixer -d 1"', config)
                self.assertIn('"on-scroll-down": "pamixer -i 1"', config)
                self.assertIn('"on-click": "tlpui"', config)
                self.assertIn("#custom-sound", style)
                self.assertIn("#custom-battery", style)
                self.assertNotIn("#pulseaudio", style)
                self.assertNotIn("#battery", style)


    def test_every_theme_sets_one_pixel_tray_spacing(self) -> None:
        root = Path(__file__).resolve().parents[1]
        theme_root = root / "src/archie/waybar-themes"

        for theme in ("cjbassi", "mechabar", "tokyonight"):
            with self.subTest(theme=theme):
                config_text = (theme_root / theme / "config").read_text(
                    encoding="utf-8"
                )
                config = json.loads(config_text.split("\n", 2)[2])
                self.assertEqual(config["tray"]["spacing"], 1)
                self.assertEqual(config["tray"]["icon-size"], 20)

    def test_every_theme_swaps_workspace_and_tray_positions(self) -> None:
        root = Path(__file__).resolve().parents[1]
        theme_root = root / "src/archie/waybar-themes"

        for theme in ("cjbassi", "mechabar", "tokyonight"):
            with self.subTest(theme=theme):
                config = (theme_root / theme / "config").read_text(encoding="utf-8")
                modules_left = config.split('"modules-left": [', 1)[1].split("]", 1)[0]
                modules_right = config.split('"modules-right": [', 1)[1].split("]", 1)[0]
                left_names = [
                    module.strip(' ",')
                    for module in modules_left.splitlines()
                    if module.strip().startswith('"')
                ]
                right_names = [
                    module.strip(' ",')
                    for module in modules_right.splitlines()
                    if module.strip().startswith('"')
                ]

                self.assertEqual(left_names[0], "tray")
                self.assertEqual(right_names[-1], "hyprland/workspaces")
                self.assertEqual(
                    [
                        module
                        for module in left_names
                        if module in {"cpu", "custom/memory", "custom/disk"}
                    ],
                    ["cpu", "custom/memory", "custom/disk"],
                )

    def test_every_theme_binds_date_clicks_to_calendar_actions(self) -> None:
        root = Path(__file__).resolve().parents[1]
        theme_root = root / "src/archie/waybar-themes"

        for theme in ("cjbassi", "mechabar", "tokyonight"):
            with self.subTest(theme=theme):
                config = (theme_root / theme / "config").read_text(encoding="utf-8")
                date_module = config.split('"clock#1": {', 1)[1].split("    },", 1)[0]

                self.assertNotIn('"on-click":', date_module)
                self.assertIn(
                    '"on-click-right": "archie system open calendar --view month --click right"', date_module
                )
