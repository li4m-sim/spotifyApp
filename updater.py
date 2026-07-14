import os
import sys
import subprocess
from datetime import date, timedelta

# Where to store the last-checked date (single line: YYYY-MM-DD)
_TIMESTAMP_FILE = os.path.join(os.path.expanduser("~"), ".spotifyapp_update_check")

# How many days between update checks
_CHECK_INTERVAL_DAYS = 30

# Path to the project root (same directory as this file)
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def check_and_update() -> None:
    """
    Check if 30 days have passed since the last update check.
    If yes, fetch from origin and pull if behind.
    Restarts the app automatically if an update was applied.
    All errors are caught silently — startup is never blocked.
    """
    if not _is_due():
        return

    try:
        _run_update()
    except Exception:
        # Never block startup on any error
        pass

    _write_timestamp()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_due() -> bool:
    """Return True if ≥30 days have passed since the last check."""
    try:
        if not os.path.exists(_TIMESTAMP_FILE):
            return True
        with open(_TIMESTAMP_FILE, "r") as f:
            last = date.fromisoformat(f.read().strip())
        return (date.today() - last) >= timedelta(days=_CHECK_INTERVAL_DAYS)
    except Exception:
        return True


def _write_timestamp() -> None:
    """Write today's date to the timestamp file."""
    try:
        with open(_TIMESTAMP_FILE, "w") as f:
            f.write(date.today().isoformat())
    except Exception:
        pass


def _run(cmd: list) -> subprocess.CompletedProcess:
    """Run a subprocess command in the project directory, capturing output."""
    return subprocess.run(
        cmd,
        cwd=_PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=15,
    )


def _run_update() -> None:
    """Fetch from origin, check if behind, pull and restart if needed."""
    # Silently fetch latest refs
    fetch = _run(["git", "fetch", "origin"])
    if fetch.returncode != 0:
        return

    # Compare local HEAD to origin/main
    local = _run(["git", "rev-parse", "HEAD"])
    remote = _run(["git", "rev-parse", "origin/main"])

    if local.returncode != 0 or remote.returncode != 0:
        return

    local_sha = local.stdout.strip()
    remote_sha = remote.stdout.strip()

    if local_sha == remote_sha:
        # Already up to date — just update the timestamp
        return

    # Remote is ahead — pull and restart
    print("Updating to latest version...")
    pull = _run(["git", "pull", "origin", "main"])
    if pull.returncode != 0:
        return

    _write_timestamp()
    print("Restarting...")

    # Replace the current process with a fresh one
    os.execv(sys.executable, [sys.executable] + sys.argv)
