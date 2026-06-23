import argparse
from collections.abc import Sequence

from archie.applet import add_applet_parser
from archie.downgrade import add_downgrade_parser
from archie.gui import add_gui_parser
from archie.system import add_system_parser


class HelpAllAction(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[str] | None,
        option_string: str | None = None,
    ) -> None:
        print(format_help_all(parser))
        parser.exit()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="archie",
        description="Archie repository maintenance tools.",
    )
    parser.add_argument(
        "--help-all",
        action=HelpAllAction,
        nargs=0,
        help="Show all commands hierarchically and exit.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_applet_parser(subparsers)
    add_downgrade_parser(subparsers)
    add_gui_parser(subparsers)
    add_system_parser(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def format_help_all(parser: argparse.ArgumentParser) -> str:
    lines = [parser.prog]
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            lines.extend(format_subparser_action(action, indent=2))
    return "\n".join(lines)


def format_subparser_action(
    action: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    indent: int,
) -> list[str]:
    lines: list[str] = []
    seen_parsers: set[int] = set()
    help_by_name = subparser_help_by_name(action)
    for name, subparser in action.choices.items():
        if id(subparser) in seen_parsers:
            continue
        seen_parsers.add(id(subparser))
        lines.append(format_command_line(name, subparser, help_text=help_by_name.get(name), indent=indent))
        for subaction in subparser._actions:
            if isinstance(subaction, argparse._SubParsersAction):
                lines.extend(format_subparser_action(subaction, indent=indent + 2))
    return lines


def subparser_help_by_name(
    action: argparse._SubParsersAction[argparse.ArgumentParser],
) -> dict[str, str]:
    return {
        str(choice_action.dest): str(choice_action.help)
        for choice_action in action._choices_actions
        if choice_action.help is not None
    }


def format_command_line(
    name: str,
    parser: argparse.ArgumentParser,
    *,
    help_text: str | None,
    indent: int,
) -> str:
    description = parser.description or help_text
    if description:
        return f"{' ' * indent}{name} - {description}"
    return f"{' ' * indent}{name}"
