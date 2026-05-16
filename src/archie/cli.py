import argparse
from collections.abc import Sequence

from archie.downgrade import add_downgrade_parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="archie",
        description="Archie repository maintenance tools.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_downgrade_parser(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
