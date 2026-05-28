import argparse
import datetime as dt
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from archie.downgrade import (
    PackageRequest,
    build_pacman_command,
    format_shell_command,
    package_filename_matches,
    parse_archive_index,
    parse_package_request,
    parse_target,
    resolve_packages,
    run_downgrade,
)


ARCHIVE_HTML = """
<html><body><pre>
<a href="../">../</a>
<a href="linux-lts-6.12.20-1-x86_64.pkg.tar.zst">linux-lts-6.12.20-1-x86_64.pkg.tar.zst</a> 2026-01-01 10:00 100M
<a href="linux-lts-6.12.20-1-x86_64.pkg.tar.zst.sig">linux-lts-6.12.20-1-x86_64.pkg.tar.zst.sig</a> 2026-01-01 10:00 1K
<a href="linux-lts-6.12.21-1-aarch64.pkg.tar.zst">linux-lts-6.12.21-1-aarch64.pkg.tar.zst</a> 2026-01-02 10:00 100M
<a href="linux-lts-6.12.22-1-x86_64.pkg.tar.zst">linux-lts-6.12.22-1-x86_64.pkg.tar.zst</a> 2026-01-03 10:00 100M
</pre></body></html>
"""

LIVE_STYLE_LINUX_LTS_HTML = """
<html><body><pre>
<a href="linux-lts-6.18.26-2-x86_64.pkg.tar.zst">linux-lts-6.18.26-2-x86_64.pkg.tar.zst</a>             01-May-2026 16:33    144M
<a href="linux-lts-6.18.27-1-x86_64.pkg.tar.zst">linux-lts-6.18.27-1-x86_64.pkg.tar.zst</a>             07-May-2026 17:54    144M
<a href="linux-lts-6.18.28-1-x86_64.pkg.tar.zst">linux-lts-6.18.28-1-x86_64.pkg.tar.zst</a>             08-May-2026 07:23    144M
<a href="linux-lts-6.18.28-1-x86_64.pkg.tar.zst.sig">linux-lts-6.18.28-1-x86_64.pkg.tar.zst.sig</a>         08-May-2026 07:23     119
<a href="linux-lts-6.18.29-1-x86_64.pkg.tar.zst">linux-lts-6.18.29-1-x86_64.pkg.tar.zst</a>             11-May-2026 08:08    144M
</pre></body></html>
"""

LIVE_STYLE_LINUX_LTS_HEADERS_HTML = """
<html><body><pre>
<a href="linux-lts-headers-6.18.27-1-x86_64.pkg.tar.zst">linux-lts-headers-6.18.27-1-x86_64.pkg.tar.zst</a>     07-May-2026 17:54    25M
<a href="linux-lts-headers-6.18.28-1-x86_64.pkg.tar.zst">linux-lts-headers-6.18.28-1-x86_64.pkg.tar.zst</a>     08-May-2026 07:23    25M
<a href="linux-lts-headers-6.18.29-1-x86_64.pkg.tar.zst">linux-lts-headers-6.18.29-1-x86_64.pkg.tar.zst</a>     11-May-2026 08:08    25M
</pre></body></html>
"""

PINNED_LINUX_LTS_HTML = """
<html><body><pre>
<a href="linux-lts-6.6.11-1-x86_64.pkg.tar.zst">linux-lts-6.6.11-1-x86_64.pkg.tar.zst</a> 2024-01-01 10:00 100M
<a href="linux-lts-6.6.12-1-x86_64.pkg.tar.zst">linux-lts-6.6.12-1-x86_64.pkg.tar.zst</a> 2024-01-02 10:00 100M
<a href="linux-lts-6.6.12-1-x86_64.pkg.tar.zst.sig">linux-lts-6.6.12-1-x86_64.pkg.tar.zst.sig</a> 2024-01-02 10:00 1K
<a href="linux-lts-6.6.12-1-aarch64.pkg.tar.zst">linux-lts-6.6.12-1-aarch64.pkg.tar.zst</a> 2024-01-02 10:00 100M
<a href="linux-lts-6.6.13-1-x86_64.pkg.tar.zst">linux-lts-6.6.13-1-x86_64.pkg.tar.zst</a> 2024-01-03 10:00 100M
</pre></body></html>
"""

PINNED_LINUX_LTS_HEADERS_HTML = """
<html><body><pre>
<a href="linux-lts-headers-6.6.12-1-x86_64.pkg.tar.zst">linux-lts-headers-6.6.12-1-x86_64.pkg.tar.zst</a> 2024-01-02 10:00 25M
<a href="linux-lts-headers-6.6.13-1-x86_64.pkg.tar.zst">linux-lts-headers-6.6.13-1-x86_64.pkg.tar.zst</a> 2024-01-03 10:00 25M
</pre></body></html>
"""


class TargetParsingTest(unittest.TestCase):
    def test_parse_absolute_date_as_end_of_day(self) -> None:
        self.assertEqual(
            parse_target("2026-01-01"),
            dt.datetime(2026, 1, 1, 23, 59, 59, 999999),
        )

    def test_parse_relative_days(self) -> None:
        now = dt.datetime(2026, 1, 10, 12, 0)
        self.assertEqual(parse_target("7d", now=now), dt.datetime(2026, 1, 3, 12, 0))

    def test_parse_relative_hours(self) -> None:
        now = dt.datetime(2026, 1, 10, 12, 0)
        self.assertEqual(parse_target("4h", now=now), dt.datetime(2026, 1, 10, 8, 0))

    def test_rejects_invalid_target(self) -> None:
        with self.assertRaises(ValueError):
            parse_target("yesterday")


class PackageRequestParsingTest(unittest.TestCase):
    def test_parse_bare_package_request(self) -> None:
        self.assertEqual(parse_package_request("linux-lts"), PackageRequest(package="linux-lts"))

    def test_parse_pinned_package_request(self) -> None:
        self.assertEqual(
            parse_package_request("linux-lts=6.6.12-1"),
            PackageRequest(package="linux-lts", version="6.6.12-1"),
        )

    def test_rejects_empty_package_name_for_pin(self) -> None:
        with self.assertRaises(ValueError):
            parse_package_request("=6.6.12-1")

    def test_rejects_empty_version_for_pin(self) -> None:
        with self.assertRaises(ValueError):
            parse_package_request("linux-lts=")


class ArchiveParsingTest(unittest.TestCase):
    def test_parse_archive_index_keeps_matching_package_archives(self) -> None:
        candidates = parse_archive_index(
            ARCHIVE_HTML,
            package_url="https://archive.archlinux.org/packages/l/linux-lts/",
            package="linux-lts",
        )

        self.assertEqual([candidate.filename for candidate in candidates], [
            "linux-lts-6.12.20-1-x86_64.pkg.tar.zst",
            "linux-lts-6.12.22-1-x86_64.pkg.tar.zst",
        ])

    def test_parse_archive_index_accepts_live_archive_timestamp_format(self) -> None:
        candidates = parse_archive_index(
            LIVE_STYLE_LINUX_LTS_HTML,
            package_url="https://archive.archlinux.org/packages/l/linux-lts/",
            package="linux-lts",
        )

        self.assertEqual(
            [candidate.timestamp for candidate in candidates],
            [
                dt.datetime(2026, 5, 1, 16, 33),
                dt.datetime(2026, 5, 7, 17, 54),
                dt.datetime(2026, 5, 8, 7, 23),
                dt.datetime(2026, 5, 11, 8, 8),
            ],
        )

    def test_package_filename_matching_handles_hyphenated_names(self) -> None:
        self.assertTrue(
            package_filename_matches("linux-lts-headers-6.12.20-1-x86_64.pkg.tar.zst", "linux-lts-headers")
        )
        self.assertFalse(
            package_filename_matches("linux-lts-headers-6.12.20-1-aarch64.pkg.tar.zst", "linux-lts-headers")
        )
        self.assertFalse(
            package_filename_matches("linux-lts-headers-6.12.20-1-x86_64.pkg.tar.zst.sig", "linux-lts-headers")
        )


class ResolutionTest(unittest.TestCase):
    def test_resolve_packages_selects_newest_candidate_at_or_before_target(self) -> None:
        def fetcher(url: str) -> str:
            return ARCHIVE_HTML

        resolutions = resolve_packages(
            packages=["linux-lts"],
            target=dt.datetime(2026, 1, 2, 23, 59),
            archive_url="https://archive.archlinux.org",
            fetcher=fetcher,
        )

        self.assertEqual(len(resolutions), 1)
        self.assertEqual(
            resolutions[0].url,
            "https://archive.archlinux.org/packages/l/linux-lts/linux-lts-6.12.20-1-x86_64.pkg.tar.zst",
        )

    def test_resolve_packages_selects_live_style_candidate_from_seven_days_ago(self) -> None:
        def fetcher(url: str) -> str:
            return LIVE_STYLE_LINUX_LTS_HTML

        resolutions = resolve_packages(
            packages=["linux-lts"],
            target=dt.datetime(2026, 5, 8, 20, 0, 10),
            archive_url="https://archive.archlinux.org",
            fetcher=fetcher,
        )

        self.assertEqual(len(resolutions), 1)
        self.assertEqual(
            resolutions[0].url,
            "https://archive.archlinux.org/packages/l/linux-lts/linux-lts-6.18.28-1-x86_64.pkg.tar.zst",
        )

    def test_run_downgrade_prints_one_pacman_command(self) -> None:
        html_by_url = {
            "https://archive.example/packages/l/linux-lts/": ARCHIVE_HTML,
            "https://archive.example/packages/l/linux-lts-headers/": """
                <a href="linux-lts-headers-6.12.20-1-x86_64.pkg.tar.zst">linux-lts-headers-6.12.20-1-x86_64.pkg.tar.zst</a> 2026-01-01 10:00 100M
            """,
        }

        def fetcher(url: str) -> str:
            return html_by_url[url]

        args = argparse.Namespace(
            to="2026-01-01",
            archive_url="https://archive.example",
            execute=False,
            noconfirm=False,
            packages=["linux-lts", "linux-lts-headers"],
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = run_downgrade(args, fetcher=fetcher)

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            stdout.getvalue(),
            "pacman -U https://archive.example/packages/l/linux-lts/linux-lts-6.12.20-1-x86_64.pkg.tar.zst "
            "https://archive.example/packages/l/linux-lts-headers/linux-lts-headers-6.12.20-1-x86_64.pkg.tar.zst\n",
        )

    def test_run_downgrade_prints_noconfirm_when_requested(self) -> None:
        def fetcher(url: str) -> str:
            return ARCHIVE_HTML

        args = argparse.Namespace(
            to="2026-01-01",
            archive_url="https://archive.example",
            execute=False,
            noconfirm=True,
            packages=["linux-lts"],
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = run_downgrade(args, fetcher=fetcher)

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            stdout.getvalue(),
            "pacman -U --noconfirm https://archive.example/packages/l/linux-lts/linux-lts-6.12.20-1-x86_64.pkg.tar.zst\n",
        )

    def test_run_downgrade_prints_live_style_multi_package_command(self) -> None:
        html_by_url = {
            "https://archive.example/packages/l/linux-lts/": LIVE_STYLE_LINUX_LTS_HTML,
            "https://archive.example/packages/l/linux-lts-headers/": LIVE_STYLE_LINUX_LTS_HEADERS_HTML,
        }

        def fetcher(url: str) -> str:
            return html_by_url[url]

        args = argparse.Namespace(
            to="2026-05-08",
            archive_url="https://archive.example",
            execute=False,
            noconfirm=False,
            packages=["linux-lts", "linux-lts-headers"],
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = run_downgrade(args, fetcher=fetcher)

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            stdout.getvalue(),
            "pacman -U https://archive.example/packages/l/linux-lts/linux-lts-6.18.28-1-x86_64.pkg.tar.zst "
            "https://archive.example/packages/l/linux-lts-headers/linux-lts-headers-6.18.28-1-x86_64.pkg.tar.zst\n",
        )

    def test_run_downgrade_prints_pinned_package_command(self) -> None:
        def fetcher(url: str) -> str:
            return PINNED_LINUX_LTS_HTML

        args = argparse.Namespace(
            to=None,
            archive_url="https://archive.example",
            execute=False,
            noconfirm=False,
            packages=["linux-lts=6.6.12-1"],
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = run_downgrade(args, fetcher=fetcher)

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            stdout.getvalue(),
            "pacman -U https://archive.example/packages/l/linux-lts/linux-lts-6.6.12-1-x86_64.pkg.tar.zst\n",
        )

    def test_run_downgrade_applies_to_constraint_after_pinned_version(self) -> None:
        def fetcher(url: str) -> str:
            return PINNED_LINUX_LTS_HTML

        args = argparse.Namespace(
            to="2024-01-01",
            archive_url="https://archive.example",
            execute=False,
            noconfirm=False,
            packages=["linux-lts=6.6.12-1"],
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = run_downgrade(args, fetcher=fetcher)

        self.assertEqual(code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("6.6.12-1", stderr.getvalue())
        self.assertIn("at or before 2024-01-01T23:59:59.999999", stderr.getvalue())

    def test_run_downgrade_prints_mixed_pinned_and_timed_package_command(self) -> None:
        html_by_url = {
            "https://archive.example/packages/l/linux-lts/": PINNED_LINUX_LTS_HTML,
            "https://archive.example/packages/l/linux-lts-headers/": PINNED_LINUX_LTS_HEADERS_HTML,
        }

        def fetcher(url: str) -> str:
            return html_by_url[url]

        args = argparse.Namespace(
            to="2024-01-02",
            archive_url="https://archive.example",
            execute=False,
            noconfirm=False,
            packages=["linux-lts=6.6.12-1", "linux-lts-headers"],
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = run_downgrade(args, fetcher=fetcher)

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            stdout.getvalue(),
            "pacman -U https://archive.example/packages/l/linux-lts/linux-lts-6.6.12-1-x86_64.pkg.tar.zst "
            "https://archive.example/packages/l/linux-lts-headers/linux-lts-headers-6.6.12-1-x86_64.pkg.tar.zst\n",
        )

    def test_run_downgrade_fails_missing_pinned_version_without_partial_command(self) -> None:
        def fetcher(url: str) -> str:
            return PINNED_LINUX_LTS_HTML

        args = argparse.Namespace(
            to=None,
            archive_url="https://archive.example",
            execute=False,
            noconfirm=False,
            packages=["linux-lts=6.6.99-1"],
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = run_downgrade(args, fetcher=fetcher)

        self.assertEqual(code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("6.6.99-1", stderr.getvalue())

    def test_run_downgrade_rejects_malformed_pin(self) -> None:
        args = argparse.Namespace(
            to=None,
            archive_url="https://archive.example",
            execute=False,
            noconfirm=False,
            packages=["linux-lts="],
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = run_downgrade(args)

        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("invalid package value", stderr.getvalue())

    def test_run_downgrade_execute_uses_sudo_for_non_root(self) -> None:
        executed_commands: list[list[str]] = []

        def fetcher(url: str) -> str:
            return ARCHIVE_HTML

        def executor(command: list[str]) -> int:
            executed_commands.append(command)
            return 7

        args = argparse.Namespace(
            to="2026-01-01",
            archive_url="https://archive.example",
            execute=True,
            noconfirm=False,
            packages=["linux-lts"],
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = run_downgrade(args, fetcher=fetcher, executor=executor, euid=1000)

        self.assertEqual(code, 7)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(executed_commands, [[
            "sudo",
            "pacman",
            "-U",
            "https://archive.example/packages/l/linux-lts/linux-lts-6.12.20-1-x86_64.pkg.tar.zst",
        ]])

    def test_run_downgrade_execute_uses_pacman_directly_for_root(self) -> None:
        executed_commands: list[list[str]] = []

        def fetcher(url: str) -> str:
            return ARCHIVE_HTML

        def executor(command: list[str]) -> int:
            executed_commands.append(command)
            return 0

        args = argparse.Namespace(
            to="2026-01-01",
            archive_url="https://archive.example",
            execute=True,
            noconfirm=False,
            packages=["linux-lts"],
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = run_downgrade(args, fetcher=fetcher, executor=executor, euid=0)

        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(executed_commands, [[
            "pacman",
            "-U",
            "https://archive.example/packages/l/linux-lts/linux-lts-6.12.20-1-x86_64.pkg.tar.zst",
        ]])

    def test_run_downgrade_execute_passes_noconfirm(self) -> None:
        executed_commands: list[list[str]] = []

        def fetcher(url: str) -> str:
            return ARCHIVE_HTML

        def executor(command: list[str]) -> int:
            executed_commands.append(command)
            return 0

        args = argparse.Namespace(
            to="2026-01-01",
            archive_url="https://archive.example",
            execute=True,
            noconfirm=True,
            packages=["linux-lts"],
        )

        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = run_downgrade(args, fetcher=fetcher, executor=executor, euid=0)

        self.assertEqual(code, 0)
        self.assertEqual(executed_commands, [[
            "pacman",
            "-U",
            "--noconfirm",
            "https://archive.example/packages/l/linux-lts/linux-lts-6.12.20-1-x86_64.pkg.tar.zst",
        ]])

    def test_run_downgrade_fails_without_partial_command(self) -> None:
        executed_commands: list[list[str]] = []

        def fetcher(url: str) -> str:
            return ""

        def executor(command: list[str]) -> int:
            executed_commands.append(command)
            return 0

        args = argparse.Namespace(
            to="2026-01-01",
            archive_url="https://archive.example",
            execute=True,
            noconfirm=False,
            packages=["missing-package"],
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = run_downgrade(args, fetcher=fetcher, executor=executor, euid=0)

        self.assertEqual(code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("missing-package", stderr.getvalue())
        self.assertEqual(executed_commands, [])


class PacmanCommandTest(unittest.TestCase):
    def test_build_pacman_command_includes_noconfirm_before_urls(self) -> None:
        self.assertEqual(
            build_pacman_command(["https://example.test/pkg.tar.zst"], noconfirm=True),
            ["pacman", "-U", "--noconfirm", "https://example.test/pkg.tar.zst"],
        )

    def test_format_shell_command_quotes_arguments(self) -> None:
        self.assertEqual(
            format_shell_command(["pacman", "-U", "https://example.test/pkg name.pkg.tar.zst"]),
            "pacman -U 'https://example.test/pkg name.pkg.tar.zst'",
        )


if __name__ == "__main__":
    unittest.main()
