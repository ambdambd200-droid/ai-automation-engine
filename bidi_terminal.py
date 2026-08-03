"""
bidi_terminal.py — Visual-only Arabic (RTL) rendering for terminals without bidi.

NEVER mutates the original text. Only changes how text is /displayed/ in a
terminal that lacks bidirectional text support.

── HOW IT WORKS ──────────────────────────────────────────────────────────
Modern terminals on Windows (Windows Terminal, conhost) render Arabic glyph
shapes correctly (via DirectWrite) BUT often fail at:
  1. BIDI REORDERING — Arabic words display left-to-right (wrong word order)
  2. RIGHT-ALIGNMENT — Arabic text starts at the left margin

This module fixes both issues /visually only/:
  ┌──────────────────────────────────────────────┐
  │ Input  (logical):  مرحبا بك في العالم          │
  │ Output (visual):        العالم في بك مرحبا     │ (right-aligned, words reversed)
  │ Input  (logical):  Hello مرحبا بك world       │
  │ Output (visual):             Hello بك مرحبا world  │
  │ Input  (logical):  Hello world                 │ ← unchanged
  │ Input  (logical):  /help                       │ ← unchanged (slash commands)
  └──────────────────────────────────────────────┘

── USAGE ──────────────────────────────────────────────────────────────────
  # ── Pipe any command output through the filter ──
  echo "مرحبا بك" | python bidi_terminal.py
  python hunt.py --gather | python bidi_terminal.py

  # ── Import in your Python scripts ──
  from bidi_terminal import fix_line, fix_text, has_arabic, arabic_input

  # Fix a single line for display
  display_line = fix_line("مرحبا بك في العالم")

  # Fix multiline output
  print(fix_text(my_text))

  # Get right-aligned Arabic input from the user
  name = arabic_input("الاسم: ")
  # The prompt + cursor are right-aligned; the returned value is plain text.

  # ── Run a command with fixed output ──
  # python bidi_terminal.py --exec command arg1 arg2
"""

from __future__ import annotations

import os
import re
import select as _select
import shutil
import subprocess
import sys
import time as _time
from typing import List, Optional

if sys.platform == "win32":
    import msvcrt
else:
    import tty
    import termios

# ═══════════════════════════════════════════════════════════════════════════
# UNICODE RANGES
# ═══════════════════════════════════════════════════════════════════════════
# Characters used to build the Arabic-matching regex classes.
_ARABIC_CHARS = (
    "\u0600-\u06FF"  # Arabic
    "\u0750-\u077F"  # Arabic Supplement
    "\u0870-\u089F"  # Arabic Extended-B
    "\u08A0-\u08FF"  # Arabic Extended-A
    "\uFB50-\uFDFF"  # Arabic Presentation Forms-A
    "\uFE70-\uFEFF"  # Arabic Presentation Forms-B
)

# ASCII punctuation that commonly appears between Arabic words.
_ASCII_PUNCT = r"!\"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~"

# Match a single run of Arabic words (including spaces and punctuation between them).
# This ensures "مرحبا بك في" and "مرحبا! بك؟" are each captured as ONE match,
# so we can reverse the word order within the phrase.
_ARABIC_RUN_RE = re.compile(
    f"[{_ARABIC_CHARS}]+(?:[\\s{_ASCII_PUNCT}]+[{_ARABIC_CHARS}]+)*"
)

# Quick check: does a string contain ANY Arabic character?
_ARABIC_ANY_RE = re.compile(f"[{_ARABIC_CHARS}]")

# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════


def has_arabic(text: str) -> bool:
    """Return True if *text* contains any Arabic-script characters."""
    return bool(_ARABIC_ANY_RE.search(text))


def reverse_arabic_runs(text: str) -> str:
    """Reverse the order of words inside every contiguous Arabic phrase.

    An "Arabic phrase" is one or more Arabic words separated by spaces.
    Non-Arabic text (English, punctuation, numbers) is left untouched.
    Individual letters within a word are /never/ reversed.

    Examples (showing logical → visual):
        "مرحبا بك في العالم"      → "العالم في بك مرحبا"
        "Hello مرحبا بك world"    → "Hello بك مرحبا world"
        "Hello world"              → "Hello world"
        "/help"                     → "/help"

    Implementation note:
        We use re.split() with the Arabic-run pattern wrapped in a capture
        group. This gives us alternating (non-Arabic, Arabic) segments.
        Arabic segments get their words reversed; non-Arabic segments pass
        through unchanged.
    """
    # Split text into alternating non-Arabic / Arabic-run segments.
    # The capture group makes re.split() include the matched runs.
    parts = re.split(f"({_ARABIC_RUN_RE.pattern})", text)

    result: List[str] = []
    for part in parts:
        if _ARABIC_ANY_RE.match(part):
            # This is an Arabic phrase — split into words and reverse
            words = part.split()
            result.append(" ".join(reversed(words)))
        else:
            # Non-Arabic text — pass through unchanged
            result.append(part)

    return "".join(result)


def _get_terminal_width() -> int:
    """Return the current terminal width (columns), falling back to 80."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def _visible_width(text: str) -> int:
    """Display width of *text* (assumes each BMP codepoint is 1 cell)."""
    return len(text)


def fix_line(line: str, terminal_width: Optional[int] = None) -> str:
    """Apply visual-only RTL rendering to a single text line.

    Rules:
      • Empty lines, English-only lines → returned unchanged.
      • Slash commands (e.g. ``/help``)  → returned unchanged.
      • Lines containing Arabic:
        1. Arabic word runs are reversed (word order, not letter order).
        2. The line is right-aligned within *terminal_width*.
      • Trailing newline (``\\n``) is preserved.

    Args:
        line: The text line to fix (visual only — original is never mutated).
        terminal_width: Width of terminal in columns. Auto-detected if None.

    Returns:
        Visually-fixed text suitable for display in a non-bidi terminal.
    """
    if not line:
        return line

    stripped = line.rstrip("\n")

    # Leave empty lines, lines without Arabic, and slash commands as-is.
    if not stripped or not has_arabic(stripped):
        return line

    if stripped.strip().startswith("/"):
        return line

    # Reverse Arabic word runs
    fixed = reverse_arabic_runs(stripped)

    # Right-align
    tw = terminal_width if terminal_width is not None else _get_terminal_width()
    vw = _visible_width(fixed)
    if vw < tw:
        fixed = " " * (tw - vw) + fixed

    # Preserve trailing newline
    if line.endswith("\n"):
        fixed += "\n"

    return fixed


def fix_text(text: str, terminal_width: Optional[int] = None) -> str:
    """Apply the RTL rendering fix to multiline text.

    Each line is processed independently by :func:`fix_line`.
    """
    lines = text.splitlines(keepends=True)
    return "".join(fix_line(ln, terminal_width) for ln in lines)


# ═══════════════════════════════════════════════════════════════════════════
# INTERACTIVE INPUT (right-aligned Arabic input)
# ═══════════════════════════════════════════════════════════════════════════

def arabic_input(prompt: str = "",
                 terminal_width: Optional[int] = None) -> str:
    """Right-aligned text input that handles Arabic typing correctly.

    The *prompt* is displayed right-aligned. As the user types, input is
    shown right-aligned. Backspace/Enter work normally. The returned string
    is the raw, un-mutated text the user typed.

    Falls back to the built-in ``input()`` if the terminal isn't interactive
    or if we can't enable raw character reading.

    Args:
        prompt: Optional prompt string. If it contains Arabic words, they
                are visually reversed (right-aligned with the input).

    Returns:
        The user's input, un-mutated (logical-order).
    """
    try:
        return _raw_arabic_input(prompt, terminal_width)
    except Exception:
        return input(prompt)


def _raw_arabic_input(prompt: str, tw: Optional[int]) -> str:
    """Raw character-by-character input with right-aligned display."""
    tw = tw if tw is not None else _get_terminal_width()

    # Fix prompt for display
    prompt_fixed = fix_line(prompt, tw)
    display_prefix = prompt_fixed

    buf: List[str] = []
    _redraw(display_prefix, "".join(buf), tw)

    while True:
        ch = _getch()
        if ch == b"\r" or ch == b"\n":  # Enter
            print()
            return "".join(buf)
        elif ch == b"\x7f" or ch == b"\x08":  # Backspace
            if buf:
                buf.pop()
        elif ch == b"\x03":  # Ctrl+C
            raise KeyboardInterrupt
        else:
            try:
                decoded = ch.decode("utf-8")
                if decoded.isprintable() or ord(decoded) >= 0x0600:
                    buf.append(decoded)
            except UnicodeDecodeError:
                pass
        _redraw(display_prefix, "".join(buf), tw)


def _redraw(prefix: str, user_text: str, tw: int):
    """Clear the current line and redraw *prefix* + *user_text* right-aligned."""
    display_text = prefix + user_text
    vw = _visible_width(display_text)
    if vw >= tw:
        display_line = display_text
    else:
        display_line = " " * (tw - vw) + display_text
    print(f"\r{display_line}", end="", flush=True)


def _getch() -> bytes:
    """Read a single byte (or bytes for UTF-8 multi-byte) from stdin.

    On Windows uses msvcrt.getch; on Unix uses tty.setraw + sys.stdin.buffer.
    """
    if sys.platform == "win32":
        raw = msvcrt.getch()
        if raw == b"\xe0":  # Extended keys (arrows, etc.)
            raw += msvcrt.getch()
        return raw

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.buffer.read(1)
        # Multi-byte UTF-8 sequences
        if ch and (ch[0] & 0xE0) == 0xC0:
            ch += sys.stdin.buffer.read(1)
        elif ch and (ch[0] & 0xF0) == 0xE0:
            ch += sys.stdin.buffer.read(2)
        elif ch and (ch[0] & 0xF8) == 0xF0:
            ch += sys.stdin.buffer.read(3)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# ═══════════════════════════════════════════════════════════════════════════
# COMMAND-LINE INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

def _pipe_mode() -> None:
    """Read stdin line by line, fix RTL, write to stdout."""
    for raw_line in sys.stdin:
        sys.stdout.write(fix_line(raw_line))
        sys.stdout.flush()


def _exec_mode(args: List[str]) -> None:
    """Run a command, intercept stdout, fix RTL in real-time.

    Usage:
        python bidi_terminal.py --exec my_command arg1 arg2
    """
    cmd = subprocess.list2cmdline(args)
    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except FileNotFoundError:
        print(f"[bidi_terminal] Command not found: {cmd}", file=sys.stderr)
        sys.exit(1)

    if not proc.stdout:
        return

    for raw_line in iter(proc.stdout.readline, ""):
        sys.stdout.write(fix_line(raw_line))
        sys.stdout.flush()

    proc.wait()
    sys.exit(proc.returncode)


def _wrap_mode() -> None:
    """Wrap an interactive CLI tool with bidirectional I/O fixing.

    NOT RECOMMENDED ON WINDOWS — ``select.select()`` doesn't work with
    pipes/subprocess stdout on Windows. Use ``--exec`` for non-interactive
    commands, or pipe mode.

    Usage:
        python bidi_terminal.py --wrap -- your-command [args...]
    """
    argv = sys.argv[1:]
    if "--" not in argv:
        print(
            "[bidi_terminal] --wrap requires a '--' separator before the command.\n"
            "  Usage: python bidi_terminal.py --wrap -- your-command [args...]",
            file=sys.stderr,
        )
        sys.exit(1)
    sep_index = argv.index("--")
    cmd = argv[sep_index + 1:]

    if not cmd:
        print("[bidi_terminal] No command specified after '--'.", file=sys.stderr)
        sys.exit(1)

    tw = _get_terminal_width()
    cmdline = subprocess.list2cmdline(cmd)

    try:
        proc = subprocess.Popen(
            cmdline,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            bufsize=0,
        )
    except FileNotFoundError:
        print(f"[bidi_terminal] Command not found: {cmdline}", file=sys.stderr)
        sys.exit(1)

    stdout_data = b""

    while proc.poll() is None:
        # Read available stdout
        if proc.stdout:
            chunk = proc.stdout.buffer.read1(4096)
            if chunk:
                stdout_data += chunk
                while b"\n" in stdout_data:
                    line_bytes, stdout_data = stdout_data.split(b"\n", 1)
                    line = line_bytes.decode("utf-8", errors="replace")
                    sys.stdout.write(fix_line(line + "\n", tw))
                    sys.stdout.flush()

        # Forward stdin to child (keystrokes pass through unfixed)
        if sys.stdin.isatty():
            try:
                rlist, _, _ = _select.select([sys.stdin], [], [], 0.05)
                if rlist:
                    chunk = sys.stdin.buffer.read(4096)
                    if chunk and proc.stdin:
                        proc.stdin.buffer.write(chunk)
                        proc.stdin.buffer.flush()
            except Exception:
                pass

        _time.sleep(0.01)

    # Flush remaining output
    if stdout_data:
        sys.stdout.write(fix_text(stdout_data.decode("utf-8", errors="replace"), tw))

    if proc.stdout:
        for raw_line in proc.stdout:
            sys.stdout.write(fix_line(raw_line, tw))
            sys.stdout.flush()

    proc.wait()
    sys.exit(proc.returncode)


def main() -> None:
    """CLI entry point.

    Modes:
      • No args / stdin is a pipe  → pipe mode (read stdin, fix, write stdout)
      • ``--exec <cmd> [args...]`` → run command, fix its output
      • ``--wrap -- <cmd> [args]``  → wrap interactive CLI (Unix only)
    """
    if "--exec" in sys.argv:
        idx = sys.argv.index("--exec")
        args = sys.argv[idx + 1:]
        _exec_mode(args)
        return

    if "--wrap" in sys.argv:
        _wrap_mode()
        return

    if not sys.stdin.isatty():
        _pipe_mode()
        return

    # Interactive (no pipe) — show usage
    print("bidi_terminal.py — Visual-only Arabic (RTL) rendering fix", file=sys.stderr)
    print("", file=sys.stderr)
    print("USAGE:", file=sys.stderr)
    print("  pipe filter:", file=sys.stderr)
    print("    command | python bidi_terminal.py", file=sys.stderr)
    print("", file=sys.stderr)
    print("  exec mode (non-interactive):", file=sys.stderr)
    print("    python bidi_terminal.py --exec your-command", file=sys.stderr)
    print("", file=sys.stderr)
    print("  wrap mode (interactive CLI):", file=sys.stderr)
    print("    python bidi_terminal.py --wrap -- your-command [args...]", file=sys.stderr)
    print("", file=sys.stderr)
    print("  Python import:", file=sys.stderr)
    print("    from bidi_terminal import fix_line, fix_text, arabic_input", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
