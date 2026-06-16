"""Argument parsing and dispatch for the alarm clock CLI.

This module stays deliberately thin: it builds the top-level parser, lets each
command package register its own subparser(s) and handler, then dispatches to the
handler the user selected. The actual command logic lives in :mod:`alarm_clock.commands`.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .commands import foreground, manage, watch

# Order here is the order subcommands appear in ``alarm --help``.
_COMMAND_GROUPS = (foreground, manage, watch)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alarm",
        description="A small, dependency-free alarm clock for the terminal.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    for group in _COMMAND_GROUPS:
        group.register(sub)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
