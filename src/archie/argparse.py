import argparse
from typing import Any, NoReturn


class ArchieArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        subparser_actions = [
            action
            for action in self._actions
            if isinstance(action, argparse._SubParsersAction)
            and hasattr(action, "_archie_help_metavar")
        ]
        original_metavars = [(action, action.metavar) for action in subparser_actions]
        for action, _ in original_metavars:
            action.metavar = None
        try:
            super().error(message)
        finally:
            for action, metavar in original_metavars:
                action.metavar = metavar


def add_command_subparsers(
    parser: argparse.ArgumentParser,
    *,
    dest: str,
    metavar: str,
) -> argparse._SubParsersAction[Any]:
    action = parser.add_subparsers(
        dest=dest,
        metavar=metavar,
        parser_class=ArchieArgumentParser,
        required=True,
    )
    action_any: Any = action
    action_any._archie_help_metavar = metavar
    return action
