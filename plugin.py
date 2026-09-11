#!/usr/bin/env python3
"""Herdr Tab Tips plugin entrypoint.

Event hooks are short-lived. The tab-bar status command prints one compact
line. The copy-id action writes the active pane public id to the clipboard.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

MAX_LABEL_LENGTH = 48
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f\x80-\x9f]")


def herdr_binary() -> str:
    return os.environ.get("HERDR_BIN_PATH") or "herdr"


def context() -> dict:
    try:
        value = json.loads(os.environ.get("HERDR_PLUGIN_CONTEXT_JSON", "{}"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def clean(value: object, limit: int = MAX_LABEL_LENGTH) -> str:
    text = CONTROL_RE.sub("", str(value or ""))
    text = " ".join(text.split()).strip()
    return text[:limit]


def run_herdr(*args: str, timeout: float = 2.0) -> dict:
    try:
        result = subprocess.run(
            [herdr_binary(), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            return {}
        value = json.loads(result.stdout)
        return value if isinstance(value, dict) else {}
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return {}


def current_pane_id() -> str:
    data = context()
    return clean(
        data.get("focused_pane_id")
        or os.environ.get("HERDR_PANE_ID")
        or os.environ.get("HERDR_ACTIVE_PANE_ID")
    )


def pane_info(pane_id: str) -> dict:
    if not pane_id:
        return {}
    pane = run_herdr("pane", "get", pane_id).get("result", {}).get("pane", {})
    return pane if isinstance(pane, dict) else {}


def default_pane_label(pane_id: str, pane: dict) -> str:
    existing = clean(pane.get("label"))
    if existing:
        return existing
    title = clean(pane.get("terminal_title_stripped") or pane.get("terminal_title"))
    if title:
        return title
    cwd = clean(pane.get("cwd"))
    if cwd:
        name = clean(Path(cwd).name)
        if name and name != "/":
            return name
    return pane_id


def ensure_pane_label() -> None:
    pane_id = current_pane_id()
    if not pane_id:
        return
    pane = pane_info(pane_id)
    label = default_pane_label(pane_id, pane)
    if not label or clean(pane.get("label")) == label:
        return
    subprocess.run(
        [herdr_binary(), "pane", "rename", pane_id, label],
        capture_output=True,
        text=True,
        timeout=2,
        check=False,
    )


def print_active_pane() -> None:
    pane_id = clean(os.environ.get("HERDR_ACTIVE_PANE_ID"))
    if not pane_id:
        return
    pane = pane_info(pane_id)
    label = clean(pane.get("label"))
    print(f"{label} · {pane_id}" if label else pane_id, end="")


def applescript_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def run_argv(argv: list[str], stdin: str | None = None, timeout: float = 2.0) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            argv,
            input=stdin,
            text=True,
            timeout=timeout,
            check=False,
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def copy_macos_clipboard(text: str) -> bool:
    quoted = applescript_string(text)
    # Server-spawned pbcopy can exit 0 without updating the GUI pasteboard that
    # Cmd+V reads. osascript talks to the user session pasteboard directly.
    attempts = (
        ["osascript", "-e", f"set the clipboard to {quoted}"],
        [
            "osascript",
            "-e",
            "use framework \"AppKit\"",
            "-e",
            "set pb to current application's NSPasteboard's generalPasteboard()",
            "-e",
            "pb's clearContents()",
            "-e",
            f"pb's setString:{quoted} forType:(current application's NSPasteboardTypeString)",
        ],
        ["/usr/bin/pbcopy"],
        ["pbcopy"],
    )
    for argv in attempts:
        stdin = None if argv[0].endswith("osascript") else text
        result = run_argv(argv, stdin=stdin)
        if result is not None and result.returncode == 0:
            return True
    return False


def copy_to_clipboard(text: str) -> bool:
    if not text:
        return False
    if sys.platform == "darwin":
        return copy_macos_clipboard(text)
    for argv in (
        ["wl-copy"],
        ["xclip", "-selection", "clipboard"],
    ):
        result = run_argv(argv, stdin=text)
        if result is not None and result.returncode == 0:
            return True
    return False


def clipboard_contains(text: str) -> bool:
    if sys.platform == "darwin":
        result = run_argv(["osascript", "-e", "the clipboard as text"])
        if result is not None and result.returncode == 0 and result.stdout.rstrip("\n") == text:
            return True
        result = run_argv(["pbpaste"])
        return bool(result and result.returncode == 0 and result.stdout == text)
    result = run_argv(["wl-paste", "-n"]) or run_argv(
        ["xclip", "-selection", "clipboard", "-out"]
    )
    return bool(result and result.returncode == 0 and result.stdout.rstrip("\n") == text)


def copy_pane_id() -> int:
    pane_id = current_pane_id()
    if not pane_id:
        return 1
    copied = copy_to_clipboard(pane_id) and clipboard_contains(pane_id)
    title = "Copied pane ID" if copied else "Copy pane ID failed"
    body = pane_id if copied else f"clipboard unchanged · {pane_id}"
    subprocess.run(
        [
            herdr_binary(),
            "notification",
            "show",
            title,
            "--body",
            body,
            "--position",
            "top-right",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=2,
    )
    if copied:
        return 0
    print(pane_id)
    return 1


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command in {"pane-created", "pane-focused"}:
        ensure_pane_label()
        return 0
    if command == "status":
        print_active_pane()
        return 0
    if command == "copy-id":
        return copy_pane_id()
    print(
        "usage: plugin.py {pane-created|pane-focused|status|copy-id}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
