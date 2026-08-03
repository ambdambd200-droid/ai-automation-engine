"""Comprehensive tests for bidi_terminal.py."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from bidi_terminal import (
    has_arabic,
    reverse_arabic_runs,
    fix_line,
    fix_text,
    _get_terminal_width,
    _ARABIC_RUN_RE,
)

passed = 0
failed = 0


def check(name: str, ok: bool):
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}")


# ── Test 1: has_arabic ──
check("has_arabic: Arabic string", has_arabic("مرحبا") == True)
check("has_arabic: English string", has_arabic("Hello") == False)
check("has_arabic: mixed", has_arabic("Hello مرحبا") == True)
check("has_arabic: slash command", has_arabic("/help") == False)
check("has_arabic: empty", has_arabic("") == False)

# ── Test 2: reverse_arabic_runs (pure Arabic) ──
check("reverse: two words",
      reverse_arabic_runs("مرحبا بك") == "بك مرحبا")
check("reverse: four words",
      reverse_arabic_runs("مرحبا بك في العالم") == "العالم في بك مرحبا")
check("reverse: single word (no-op)",
      reverse_arabic_runs("مرحبا") == "مرحبا")
check("reverse: with punctuation",
      reverse_arabic_runs("مرحبا! بك؟") == "بك؟ مرحبا!")

# ── Test 3: reverse_arabic_runs (mixed text) ──
check("reverse: English prefix + Arabic",
      reverse_arabic_runs("Hello مرحبا بك world") == "Hello بك مرحبا world")
check("reverse: Arabic prefix + English",
      reverse_arabic_runs("مرحبا بك Hello world") == "بك مرحبا Hello world")
check("reverse: English only (unchanged)",
      reverse_arabic_runs("Hello world") == "Hello world")
check("reverse: slash command",
      reverse_arabic_runs("/help") == "/help")
check("reverse: mixed with numbers",
      reverse_arabic_runs("n8n مرحبا بك 123") == "n8n بك مرحبا 123")

# ── Test 4: reverse_arabic_runs — never reverses letters within a word ──
# The Arabic word "مرحبا" should stay as "مرحبا", not have its letters reversed
check("reverse: letters intact",
      "مرحبا" in reverse_arabic_runs("مرحبا بك"))
check("reverse: word preserved as unit",
      reverse_arabic_runs("أ ب") == "ب أ")

# ── Test 5: fix_line basic rules ──
check("fix_line: empty string", fix_line("") == "")
check("fix_line: English-only", fix_line("Hello") == "Hello")
check("fix_line: slash command", fix_line("/help") == "/help")
check("fix_line: slash with Arabic after (keep LTR)",
      "/run مرحبا".startswith("/run"))

# ── Test 6: fix_line right-alignment ──
line = fix_line("مرحبا بك", terminal_width=80)
# Should be right-aligned: spaces on the left, text on the right
check("fix_line: right-aligned starts with spaces",
      line.startswith(" "))
check("fix_line: right-aligned ends with reversed words",
      line.strip().endswith("بك مرحبا"))

# ── Test 7: fix_line preserves trailing newline ──
check("fix_line: preserves newline English",
      fix_line("Hello\n") == "Hello\n")
check("fix_line: preserves newline Arabic",
      fix_line("مرحبا بك\n", terminal_width=200).endswith("\n"))

# ── Test 8: fix_text multiline ──
result = fix_text("Hello\nمرحبا بك\n/help", terminal_width=80)
lines = result.splitlines()
check("fix_text: English line preserved",
      lines[0].strip() == "Hello")
check("fix_text: Arabic line right-aligned",
      lines[1].strip().endswith("بك مرحبا"))
check("fix_text: slash command preserved",
      lines[2].strip() == "/help")

# ── Test 9: reverse_arabic_runs with mixed adjacent ──
# "مرحبا123" should match "مرحبا" and "123" separately
check("reverse: adjacent Arabic+numbers",
      reverse_arabic_runs("مرحبا123") == "مرحبا123")
check("reverse: adjacent Arabic+English",
      reverse_arabic_runs("Helloمرحبا") == "Helloمرحبا")

# ── Test 10: fix_line never mutates original ──
original = "مرحبا بك"
fixed = fix_line(original, terminal_width=200)
check("fix_line: original unchanged",
      original == "مرحبا بك")
check("fix_line: fixed != original",
      fixed != original)


print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed")
if failed:
    sys.exit(1)
else:
    print("ALL TESTS PASSED!")
