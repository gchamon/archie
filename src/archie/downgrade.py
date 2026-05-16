import argparse
import contextlib
import datetime as dt
import os
import re
import shlex
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html import unescape
from typing import Protocol

ARCHITECTURE = "x86_64"
DEFAULT_ARCHIVE_URL = "https://archive.archlinux.org"
PACKAGE_SUFFIX = ".pkg.tar."

_RELATIVE_TARGET_RE = re.compile(r"^(?P<count>[1-9][0-9]*)(?P<unit>[dh])$")
_ABSOLUTE_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_HREF_ROW_RE = re.compile(
    r'href=["\'](?P<href>[^"\']+)["\'][^>]*>.*?</a>\s+'
    r"(?P<date>(?:\d{4}-\d{2}-\d{2})|(?:\d{2}-[A-Za-z]{3}-\d{4}))\s+"
    r"(?P<time>\d{2}:\d{2})",
    re.IGNORECASE,
)
_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


class Fetcher(Protocol):
    def __call__(self, url: str) -> str: ...


class Executor(Protocol):
    def __call__(self, command: list[str]) -> int: ...


@dataclass(frozen=True)
class PackageCandidate:
    filename: str
    timestamp: dt.datetime
    url: str


@dataclass(frozen=True)
class PackageRequest:
    package: str
    version: str | None = None


@dataclass(frozen=True)
class Resolution:
    package: str
    url: str | None
    error: str | None = None


def add_downgrade_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "downgrade",
        help="Resolve Arch Linux Archive package URLs for pacman -U.",
        description=(
            "Resolve Arch Linux Archive package URLs at or before a target time "
            "and print one pacman -U command."
        ),
    )
    parser.add_argument(
        "--to",
        default=None,
        metavar="TARGET",
        help="Target time: YYYY-MM-DD, 7d, or 4h. Defaults to now.",
    )
    parser.add_argument(
        "--archive-url",
        default=DEFAULT_ARCHIVE_URL,
        metavar="URL",
        help=f"Archive root URL. Defaults to {DEFAULT_ARCHIVE_URL}.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run the resolved downgrade with pacman instead of printing the command.",
    )
    parser.add_argument(
        "--noconfirm",
        action="store_true",
        help="Pass --noconfirm to pacman.",
    )
    parser.add_argument(
        "packages",
        metavar="PACKAGE",
        nargs="+",
        help="Package name, or PACKAGE=VERSION for an exact version-release pin.",
    )
    parser.set_defaults(func=run_downgrade)


def run_downgrade(
    args: argparse.Namespace,
    *,
    fetcher: Fetcher | None = None,
    executor: Executor | None = None,
    euid: int | None = None,
) -> int:
    try:
        package_requests = parse_package_requests(args.packages)
    except ValueError as error:
        print(f"archie downgrade: invalid package value: {error}", file=sys.stderr)
        return 2

    target = None
    if args.to is not None or any(request.version is None for request in package_requests):
        try:
            target = parse_target(args.to)
        except ValueError as error:
            print(f"archie downgrade: invalid --to value: {error}", file=sys.stderr)
            return 2

    resolutions = resolve_package_requests(
        package_requests=package_requests,
        target=target,
        archive_url=args.archive_url,
        fetcher=fetcher,
    )
    failures = [resolution for resolution in resolutions if resolution.error]
    if failures:
        for failure in failures:
            print(f"archie downgrade: {failure.package}: {failure.error}", file=sys.stderr)
        return 1

    urls = [resolution.url for resolution in resolutions if resolution.url]
    pacman_command = build_pacman_command(urls, noconfirm=args.noconfirm)
    if args.execute:
        return execute_pacman_command(pacman_command, executor=executor, euid=euid)

    print(format_shell_command(pacman_command))
    return 0


def parse_package_requests(package_values: list[str]) -> list[PackageRequest]:
    return [parse_package_request(package_value) for package_value in package_values]


def parse_package_request(package_value: str) -> PackageRequest:
    if "=" not in package_value:
        if not package_value:
            raise ValueError("package name cannot be empty")
        return PackageRequest(package=package_value)

    package, version = package_value.split("=", 1)
    if not package:
        raise ValueError(f"{package_value!r} is missing a package name")
    if not version:
        raise ValueError(f"{package_value!r} is missing a version")

    return PackageRequest(package=package, version=version)


def resolve_package_requests(
    *,
    package_requests: list[PackageRequest],
    target: dt.datetime | None,
    archive_url: str = DEFAULT_ARCHIVE_URL,
    fetcher: Fetcher | None = None,
) -> list[Resolution]:
    fetch = fetcher or fetch_url
    return [
        resolve_package_request(
            package_request,
            target=target,
            archive_url=archive_url,
            fetcher=fetch,
        )
        for package_request in package_requests
    ]


def resolve_package_request(
    package_request: PackageRequest,
    *,
    target: dt.datetime | None,
    archive_url: str,
    fetcher: Fetcher,
) -> Resolution:
    package_url = package_index_url(archive_url, package_request.package)
    try:
        html = fetcher(package_url)
    except OSError as error:
        return Resolution(
            package=package_request.package,
            url=None,
            error=f"could not fetch {package_url}: {error}",
        )

    candidates = parse_archive_index(html, package_url=package_url, package=package_request.package)
    if package_request.version is not None:
        return resolve_pinned_package(package_request, candidates, target=target)

    if target is None:
        return Resolution(
            package=package_request.package,
            url=None,
            error="timestamp target is required for unpinned packages",
        )

    return resolve_timed_package(package_request.package, candidates, target=target)


def resolve_pinned_package(
    package_request: PackageRequest,
    candidates: list[PackageCandidate],
    *,
    target: dt.datetime | None = None,
) -> Resolution:
    matches = [
        candidate
        for candidate in candidates
        if package_filename_version(candidate.filename, package_request.package) == package_request.version
    ]
    if not matches:
        return Resolution(
            package=package_request.package,
            url=None,
            error=f"no {ARCHITECTURE} archive found for version {package_request.version}",
        )

    if target is not None:
        matches = [candidate for candidate in matches if candidate.timestamp <= target]
        if not matches:
            return Resolution(
                package=package_request.package,
                url=None,
                error=(
                    f"no {ARCHITECTURE} archive found for version {package_request.version} "
                    f"at or before {target.isoformat()}"
                ),
            )

    return Resolution(
        package=package_request.package,
        url=max(matches, key=lambda candidate: candidate.timestamp).url,
    )


def resolve_timed_package(
    package: str,
    candidates: list[PackageCandidate],
    *,
    target: dt.datetime,
) -> Resolution:
    matches = [candidate for candidate in candidates if candidate.timestamp <= target]
    if not matches:
        return Resolution(
            package=package,
            url=None,
            error=f"no {ARCHITECTURE} archive found at or before {target.isoformat()}",
        )

    return Resolution(
        package=package,
        url=max(matches, key=lambda candidate: candidate.timestamp).url,
    )


def build_pacman_command(urls: list[str], *, noconfirm: bool = False) -> list[str]:
    command = ["pacman", "-U"]
    if noconfirm:
        command.append("--noconfirm")
    command.extend(urls)
    return command


def format_shell_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def execute_pacman_command(
    pacman_command: list[str],
    *,
    executor: Executor | None = None,
    euid: int | None = None,
) -> int:
    runner = executor or run_command
    effective_uid = os.geteuid() if euid is None else euid
    command = pacman_command if effective_uid == 0 else ["sudo", *pacman_command]
    return runner(command)


def run_command(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def parse_target(value: str | None, *, now: dt.datetime | None = None) -> dt.datetime:
    current = now or dt.datetime.now()
    if value is None:
        return current

    if _ABSOLUTE_DATE_RE.match(value):
        date = dt.date.fromisoformat(value)
        return dt.datetime.combine(date, dt.time(23, 59, 59, 999999))

    match = _RELATIVE_TARGET_RE.match(value)
    if match:
        count = int(match.group("count"))
        unit = match.group("unit")
        if unit == "d":
            return current - dt.timedelta(days=count)
        if unit == "h":
            return current - dt.timedelta(hours=count)

    raise ValueError(f"{value!r} must be YYYY-MM-DD, Nd, or Nh")


def resolve_packages(
    *,
    packages: list[str],
    target: dt.datetime,
    archive_url: str = DEFAULT_ARCHIVE_URL,
    fetcher: Fetcher | None = None,
) -> list[Resolution]:
    package_requests = [PackageRequest(package=package) for package in packages]
    return resolve_package_requests(
        package_requests=package_requests,
        target=target,
        archive_url=archive_url,
        fetcher=fetcher,
    )


def resolve_package(
    package: str,
    *,
    target: dt.datetime,
    archive_url: str,
    fetcher: Fetcher,
) -> Resolution:
    return resolve_package_request(
        PackageRequest(package=package),
        target=target,
        archive_url=archive_url,
        fetcher=fetcher,
    )


def package_index_url(archive_url: str, package: str) -> str:
    root = archive_url.rstrip("/") + "/"
    package_path = f"packages/{package[0]}/{package}/"
    return urllib.parse.urljoin(root, package_path)


def fetch_url(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "archie/0.1"})
    with contextlib.closing(urllib.request.urlopen(request, timeout=30)) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_archive_index(
    html: str,
    *,
    package_url: str,
    package: str,
) -> list[PackageCandidate]:
    candidates: list[PackageCandidate] = []
    for line in html.splitlines():
        match = _HREF_ROW_RE.search(line)
        if not match:
            continue
        href = unescape(match.group("href"))
        filename = urllib.parse.unquote(href.rstrip("/").rsplit("/", 1)[-1])
        if not package_filename_matches(filename, package):
            continue

        timestamp = parse_archive_timestamp(match.group("date"), match.group("time"))
        candidates.append(
            PackageCandidate(
                filename=filename,
                timestamp=timestamp,
                url=urllib.parse.urljoin(package_url, href),
            )
        )
    return candidates


def parse_archive_timestamp(date_value: str, time_value: str) -> dt.datetime:
    hour, minute = (int(part) for part in time_value.split(":", 1))
    if _ABSOLUTE_DATE_RE.match(date_value):
        date = dt.date.fromisoformat(date_value)
        return dt.datetime.combine(date, dt.time(hour, minute))

    day, month_name, year = date_value.split("-", 2)
    month = _MONTHS[month_name.lower()]
    return dt.datetime(int(year), month, int(day), hour, minute)


def package_filename_matches(filename: str, package: str) -> bool:
    return package_filename_version(filename, package) is not None


def package_filename_version(filename: str, package: str) -> str | None:
    if filename.endswith(".sig"):
        return None
    if not filename.startswith(f"{package}-"):
        return None

    marker_index = filename.find(PACKAGE_SUFFIX)
    if marker_index == -1:
        return None

    stem = filename[:marker_index]
    with_arch = stem.rsplit("-", 1)
    if len(with_arch) != 2:
        return None

    name_version_release, architecture = with_arch
    if architecture != ARCHITECTURE:
        return None

    version = name_version_release.removeprefix(f"{package}-")
    return version or None

