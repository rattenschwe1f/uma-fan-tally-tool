import contextlib
import os
import subprocess
import sys
import tempfile
from importlib.resources import files
from pathlib import Path


def binary_dir() -> Path:
    """Default location for user-facing files (config). Frozen binaries use
    the .exe's parent directory; if that's under the OS temp dir (Windows
    zip-preview launches a copy from %TEMP% without proper extraction),
    fall back to ~/uma-tally-tool so the config doesn't vanish on cleanup."""
    if not getattr(sys, "frozen", False):
        return Path.cwd()
    exe_dir = Path(sys.executable).parent.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    try:
        exe_dir.relative_to(temp_root)
    except ValueError:
        return exe_dir
    return Path.home() / "uma-tally-tool"


def write_starter_config(target: Path, *, template_name: str = "config.example.env") -> Path:
    """Copy a bundled starter config to `target`."""
    template = files("uma_tally_tool").joinpath(template_name).read_text()
    target.write_text(template)
    return target


def open_in_editor(path: Path) -> bool:
    """Open `path` in the user's default text editor. Best effort: returns
    True on apparent success, False if no opener was available."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
            return True
        if sys.platform == "darwin":
            return subprocess.run(["open", str(path)], check=False).returncode == 0
        return subprocess.run(["xdg-open", str(path)], check=False).returncode == 0
    except (OSError, FileNotFoundError):
        return False


def pause_before_exit() -> None:
    """Block until the user presses Enter, so a double-click console window
    doesn't close before they can read the message. No-op when stdin isn't
    a TTY (cron, CI, piped invocations)."""
    if not sys.stdin.isatty():
        return
    with contextlib.suppress(EOFError, KeyboardInterrupt):
        input("\nPress Enter to close...")
