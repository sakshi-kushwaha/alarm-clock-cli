"""CLI command handlers, grouped by concern.

Each module in this package owns its argparse subparser(s) *and* the handler(s)
that back them, and exposes a ``register(subparsers)`` function so ``cli.py`` can
wire everything up without knowing the details:

* :mod:`foreground` -- ``set`` / ``timer`` (block in the terminal, then ring)
* :mod:`manage`     -- ``add`` / ``list`` / ``remove`` / ``enable`` / ``disable``
* :mod:`watch`      -- ``run`` (foreground watcher over saved alarms)
"""

from __future__ import annotations

import sys

__all__ = ["fail"]


def fail(message: object, code: int = 2) -> int:
    """Print a user-facing error to stderr and return an exit code.

    Centralises the ``error: ...`` formatting so every command reports failures
    the same way. ``code`` defaults to 2 (bad input); pass 1 for "not found".
    """
    print(f"error: {message}", file=sys.stderr)
    return code
