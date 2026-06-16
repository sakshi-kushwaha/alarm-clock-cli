"""Best-effort, cross-platform alarm sound.

Ringing must never crash the app: every backend is wrapped so failures fall back
to the terminal bell. Backends are chosen by platform.
"""

from __future__ import annotations

import shutil
import subprocess
import sys

__all__ = ["ring"]


def _bell(times: int) -> None:
    """The universal fallback: write the ASCII bell to the terminal."""
    sys.stdout.write("\a" * times)
    sys.stdout.flush()


def _macos(times: int) -> bool:
    afplay = shutil.which("afplay")
    if not afplay:
        return False
    sound = "/System/Library/Sounds/Glass.aiff"
    for _ in range(times):
        subprocess.run([afplay, sound], check=False)
    return True


def _windows(times: int) -> bool:
    try:
        import winsound  # type: ignore
    except ImportError:
        return False
    for _ in range(times):
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    return True


def _linux(times: int) -> bool:
    for player in ("paplay", "aplay"):
        exe = shutil.which(player)
        if not exe:
            continue
        candidates = (
            "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
            "/usr/share/sounds/freedesktop/stereo/complete.oga",
        )
        for sound in candidates:
            for _ in range(times):
                subprocess.run([exe, sound], check=False)
            return True
    return False


def ring(times: int = 3, no_sound: bool = False) -> None:
    """Make an alarm noise ``times`` times. Always safe to call.

    When ``no_sound`` is true, nothing is emitted (useful for tests/scripting).
    """
    if no_sound:
        return
    try:
        if sys.platform == "darwin":
            played = _macos(times)
        elif sys.platform.startswith("win"):
            played = _windows(times)
        else:
            played = _linux(times)
        if not played:
            _bell(times)
    except Exception:
        # Sound is never worth crashing over.
        try:
            _bell(times)
        except Exception:
            pass
