#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Herdr Tab Tips plugin entrypoint.

Event hooks are short-lived. The tab-bar status command prints one compact
line. The copy-id action writes the active pane public id to the clipboard.

Portable across Python 2.7 and 3.6+ so it also runs on older dev machines.
"""

import collections
import json
import os
import re
import subprocess
import sys
import threading

PY2 = sys.version_info[0] == 2
text_type = unicode if PY2 else str  # noqa: F821

MAX_LABEL_LENGTH = 48
CONTROL_RE = re.compile(u"[\x00-\x1f\x7f\x80-\x9f]")
SEP = u" \u00b7 "
Result = collections.namedtuple("Result", "returncode stdout stderr")


def to_text(value):
    if value is None:
        return u""
    if isinstance(value, text_type):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return text_type(value)


def write(text, stream=None):
    stream = stream or sys.stdout
    getattr(stream, "buffer", stream).write(to_text(text).encode("utf-8"))
    stream.flush()


def run_argv(argv, stdin=None, timeout=2.0):
    """Run argv, return Result or None. Args are passed as UTF-8 bytes."""
    try:
        proc = subprocess.Popen(
            [to_text(a).encode("utf-8") for a in argv],
            stdin=subprocess.PIPE if stdin is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError:
        return None
    timer = threading.Timer(timeout, proc.kill)
    timer.daemon = True
    timer.start()
    try:
        data = to_text(stdin).encode("utf-8") if stdin is not None else None
        out, err = proc.communicate(data)
    except Exception:
        return None
    finally:
        timer.cancel()
    return Result(proc.returncode, to_text(out), to_text(err))


def herdr_binary():
    return os.environ.get("HERDR_BIN_PATH") or "herdr"


def context():
    try:
        value = json.loads(to_text(os.environ.get("HERDR_PLUGIN_CONTEXT_JSON", "{}")))
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def clean(value, limit=MAX_LABEL_LENGTH):
    text = CONTROL_RE.sub(u"", to_text(value or u""))
    return u" ".join(text.split()).strip()[:limit]


def run_herdr(*args):
    result = run_argv([herdr_binary()] + list(args))
    if result is None or result.returncode != 0:
        return {}
    try:
        value = json.loads(result.stdout)
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def current_pane_id():
    data = context()
    return clean(
        data.get("focused_pane_id")
        or os.environ.get("HERDR_PANE_ID")
        or os.environ.get("HERDR_ACTIVE_PANE_ID")
    )


def pane_info(pane_id):
    if not pane_id:
        return {}
    pane = run_herdr("pane", "get", pane_id).get("result", {}).get("pane", {})
    return pane if isinstance(pane, dict) else {}


def default_pane_label(pane_id, pane):
    existing = clean(pane.get("label"))
    if existing:
        return existing
    title = clean(pane.get("terminal_title_stripped") or pane.get("terminal_title"))
    if title:
        return title
    cwd = clean(pane.get("cwd"))
    if cwd:
        name = clean(os.path.basename(cwd.rstrip(u"/")))
        if name and name != u"/":
            return name
    return pane_id


def ensure_pane_label():
    pane_id = current_pane_id()
    if not pane_id:
        return
    pane = pane_info(pane_id)
    label = default_pane_label(pane_id, pane)
    if not label or clean(pane.get("label")) == label:
        return
    run_argv([herdr_binary(), "pane", "rename", pane_id, label])


def print_active_pane():
    pane_id = clean(os.environ.get("HERDR_ACTIVE_PANE_ID"))
    if not pane_id:
        return
    label = clean(pane_info(pane_id).get("label"))
    write(label + SEP + pane_id if label else pane_id)


def applescript_string(text):
    return u'"' + text.replace(u"\\", u"\\\\").replace(u'"', u'\\"') + u'"'


def copy_macos_clipboard(text):
    quoted = applescript_string(text)
    # Server-spawned pbcopy can exit 0 without updating the GUI pasteboard that
    # Cmd+V reads. osascript talks to the user session pasteboard directly.
    attempts = (
        ["osascript", "-e", u"set the clipboard to " + quoted],
        [
            "osascript",
            "-e",
            'use framework "AppKit"',
            "-e",
            "set pb to current application's NSPasteboard's generalPasteboard()",
            "-e",
            "pb's clearContents()",
            "-e",
            u"pb's setString:" + quoted
            + u" forType:(current application's NSPasteboardTypeString)",
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


def copy_to_clipboard(text):
    if not text:
        return False
    if sys.platform == "darwin":
        return copy_macos_clipboard(text)
    for argv in (["wl-copy"], ["xclip", "-selection", "clipboard"]):
        result = run_argv(argv, stdin=text)
        if result is not None and result.returncode == 0:
            return True
    return False


def clipboard_contains(text):
    if sys.platform == "darwin":
        result = run_argv(["osascript", "-e", "the clipboard as text"])
        if result is not None and result.returncode == 0 and result.stdout.rstrip(u"\n") == text:
            return True
        result = run_argv(["pbpaste"])
        return bool(result and result.returncode == 0 and result.stdout == text)
    result = run_argv(["wl-paste", "-n"]) or run_argv(
        ["xclip", "-selection", "clipboard", "-out"]
    )
    return bool(result and result.returncode == 0 and result.stdout.rstrip(u"\n") == text)


def copy_pane_id():
    pane_id = current_pane_id()
    if not pane_id:
        return 1
    copied = copy_to_clipboard(pane_id) and clipboard_contains(pane_id)
    title = u"Copied pane ID" if copied else u"Copy pane ID failed"
    body = pane_id if copied else u"clipboard unchanged" + SEP + pane_id
    run_argv(
        [herdr_binary(), "notification", "show", title, "--body", body,
         "--position", "top-right"]
    )
    if copied:
        return 0
    write(pane_id + u"\n")
    return 1


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command in ("pane-created", "pane-focused"):
        ensure_pane_label()
        return 0
    if command == "status":
        print_active_pane()
        return 0
    if command == "copy-id":
        return copy_pane_id()
    write(u"usage: plugin.py {pane-created|pane-focused|status|copy-id}\n", sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
