"""
desktop_mcp_server.py — MCP Server for desktop automation (mouse, keyboard, screenshots).

Provides granular MCP tools for AI agents to control the desktop like a human,
using pyautogui with natural delays, coordinate validation, and failsafe.

── PROTOCOL ───────────────────────────────────────────────────────────────
Model Context Protocol (MCP) — JSON-RPC 2.0 over stdio.
Compatible with any MCP client (Claude Desktop, Cursor, opencode, etc.).

── TOOLS ──────────────────────────────────────────────────────────────────
  mouse_move(x, y)           Move mouse to coordinates (human-like arc)
  mouse_click(x?, y?)        Click at position (or current)
  mouse_double_click(x?, y?) Double click
  mouse_drag(start_x, start_y, end_x, end_y)  Drag from one point to another
  keyboard_type(text)        Type text with human-like interval
  keyboard_press(key)        Press a single key (enter, tab, escape, etc.)
  keyboard_hotkey(keys)      Press key combination (ctrl, c)
  scroll(amount)             Scroll (positive=down, negative=up)
  screenshot()               Take screenshot, return as base64 image
  get_screen_size()          Return display dimensions
  wait(seconds)              Sleep for N seconds
  locate_on_screen(image_path, confidence?)  Find image location on screen

── USAGE ──────────────────────────────────────────────────────────────────
  # Standalone (stdio MCP server — for AI clients)
  python desktop_mcp_server.py

  # Test (list all tools and exit)
  python desktop_mcp_server.py --test

── INTEGRATION ────────────────────────────────────────────────────────────
  In opencode.jsonc or any MCP client config:
  {
    "mcpServers": {
      "desktop": {
        "command": "python",
        "args": ["C:\\Users\\A\\Desktop\\Money\\desktop_mcp_server.py"]
      }
    }
  }
"""

from __future__ import annotations

import asyncio
import base64
import io
import os
import random as _random
import sys
import time as _time
import traceback
from pathlib import Path
from typing import Any, Optional

# Clipboard support for non-Latin text typing
import pyperclip

# Ensure pyautogui's failsafe always works
import pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05  # small pause between pyautogui actions

# ── MCP SDK ──
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    ImageContent,
    TextContent,
    Tool,
    CallToolResult,
)

# ── Project imports ──
WORKSPACE = Path(r"C:\Users\A\Desktop\Money")
LOG_FILE = WORKSPACE / "desktop_mcp.log"

# ── Screen bounds (cached) ──
SCREEN_W, SCREEN_H = pyautogui.size()

# ── Human-like behavior settings ──
MOVE_DURATION = 0.15     # seconds for mouse movement (human-like arc)
TYPE_INTERVAL = 0.02     # seconds between keystrokes
CLICK_PAUSE = 0.2        # pause after click

# ── Security ──
BLOCKED_EXTENSIONS = {".zip", ".exe", ".rar", ".scr", ".bat", ".msi", ".cmd", ".com"}
PRIVACY_PATHS = {
    Path(r"C:\Users\A\Desktop\AI-OS-Agent\.env"),
    Path(r"C:\Users\A\.ssh"),
    Path(r"C:\Users\A\.config\opencode"),
}


# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

def log(msg: str):
    """Append to log file (stderr is reserved for MCP protocol)."""
    ts = _time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def validate_coords(x: int, y: int) -> None:
    """Raise ValueError if coordinates are out of screen bounds."""
    if not (0 <= x <= SCREEN_W and 0 <= y <= SCREEN_H):
        raise ValueError(
            f"Coordinates ({x}, {y}) out of bounds ({SCREEN_W}x{SCREEN_H})"
        )


def validate_text(text: str) -> None:
    """Raise ValueError if text contains blocked file extensions."""
    lower = text.lower()
    for ext in BLOCKED_EXTENSIONS:
        if ext in lower:
            raise ValueError(
                f"Text contains blocked file extension '{ext}'. "
                "Request Google Docs / GitHub links instead."
            )


def is_privacy_path(path: str) -> bool:
    """Check if a path contains sensitive user information."""
    for pp in PRIVACY_PATHS:
        if pp in Path(path).resolve().parents:
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════════
# MCP SERVER DEFINITION
# ═══════════════════════════════════════════════════════════════════════════

server = Server("desktop-automation")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="mouse_move",
            description="Move the mouse cursor to specified screen coordinates with human-like motion.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "X coordinate (0 to screen width)"},
                    "y": {"type": "number", "description": "Y coordinate (0 to screen height)"},
                },
                "required": ["x", "y"],
            },
        ),
        Tool(
            name="mouse_click",
            description="Click at the current cursor position, or at specified coordinates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "Optional X coordinate"},
                    "y": {"type": "number", "description": "Optional Y coordinate"},
                    "button": {
                        "type": "string",
                        "enum": ["left", "middle", "right"],
                        "description": "Mouse button (default: left)",
                    },
                },
            },
        ),
        Tool(
            name="mouse_double_click",
            description="Double-click at the current cursor position, or at specified coordinates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "Optional X coordinate"},
                    "y": {"type": "number", "description": "Optional Y coordinate"},
                },
            },
        ),
        Tool(
            name="mouse_drag",
            description="Drag the mouse from start coordinates to end coordinates (like a human dragging).",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_x": {"type": "number", "description": "Starting X coordinate"},
                    "start_y": {"type": "number", "description": "Starting Y coordinate"},
                    "end_x": {"type": "number", "description": "Ending X coordinate"},
                    "end_y": {"type": "number", "description": "Ending Y coordinate"},
                    "duration": {
                        "type": "number",
                        "description": "Duration in seconds (default: 0.3)",
                    },
                    "button": {
                        "type": "string",
                        "enum": ["left", "middle", "right"],
                        "description": "Mouse button to drag with (default: left)",
                    },
                },
                "required": ["start_x", "start_y", "end_x", "end_y"],
            },
        ),
        Tool(
            name="keyboard_type",
            description="Type text with human-like keystroke intervals. Supports Arabic and special characters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to type. Use \\\\n for newlines.",
                    },
                    "interval": {
                        "type": "number",
                        "description": "Interval between keystrokes in seconds (default: 0.02, human-like)",
                    },
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="keyboard_press",
            description="Press and release a keyboard key. Common keys: enter, tab, escape, backspace, delete, up, down, left, right, home, end, pageup, pagedown, f1-f12.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key name to press"},
                },
                "required": ["key"],
            },
        ),
        Tool(
            name="keyboard_hotkey",
            description="Press multiple keys simultaneously (e.g., ctrl+c, alt+tab, ctrl+shift+esc).",
            inputSchema={
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keys to press together, e.g. ['ctrl', 'c']",
                    },
                },
                "required": ["keys"],
            },
        ),
        Tool(
            name="scroll",
            description="Scroll the mouse wheel. Positive = scroll down, negative = scroll up.",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Number of clicks to scroll (positive=down, negative=up)",
                    },
                },
                "required": ["amount"],
            },
        ),
        Tool(
            name="screenshot",
            description="Take a screenshot of the entire screen and return it as a base64-encoded image.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_screen_size",
            description="Get the screen resolution (width x height). Useful before moving/clicking.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="wait",
            description="Wait/sleep for a specified number of seconds. Useful between actions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "seconds": {
                        "type": "number",
                        "description": "Number of seconds to wait",
                    },
                },
                "required": ["seconds"],
            },
        ),
        Tool(
            name="locate_on_screen",
            description="Locate an image on the screen and return its position. Useful for finding buttons/icons.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Path to the image file to search for",
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Matching confidence 0-1 (default: 0.8)",
                    },
                },
                "required": ["image_path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    log(f"Tool called: {name} with {arguments}")
    try:
        result = await _execute_tool(name, arguments)
        log(f"Tool {name} succeeded")
        return CallToolResult(content=result)
    except ValueError as e:
        log(f"Tool {name} validation error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"VALIDATION ERROR: {e}")],
            isError=True,
        )
    except pyautogui.FailSafeException:
        msg = "ABORTED — Mouse moved to screen corner (failsafe triggered)"
        log(msg)
        return CallToolResult(
            content=[TextContent(type="text", text=msg)],
            isError=True,
        )
    except Exception as e:
        log(f"Tool {name} error: {e}\n{traceback.format_exc()}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"ERROR: {e}\n{traceback.format_exc()}")],
            isError=True,
        )


async def _execute_tool(name: str, args: dict) -> list:
    """Execute a tool and return a list of content items."""
    # ── Mouse tools ──
    if name == "mouse_move":
        x, y = int(args["x"]), int(args["y"])
        validate_coords(x, y)
        pyautogui.moveTo(x, y, duration=MOVE_DURATION)
        return [TextContent(type="text", text=f"Moved mouse to ({x}, {y})")]

    if name == "mouse_click":
        if "x" in args and "y" in args:
            x, y = int(args["x"]), int(args["y"])
            validate_coords(x, y)
            pyautogui.moveTo(x, y, duration=MOVE_DURATION)
        button = args.get("button", "left")
        _time.sleep(0.05)
        pyautogui.click(button=button)
        _time.sleep(CLICK_PAUSE)
        return [TextContent(type="text", text=f"Clicked {button} button")]

    if name == "mouse_double_click":
        if "x" in args and "y" in args:
            x, y = int(args["x"]), int(args["y"])
            validate_coords(x, y)
            pyautogui.moveTo(x, y, duration=MOVE_DURATION)
        pyautogui.doubleClick()
        _time.sleep(CLICK_PAUSE)
        return [TextContent(type="text", text="Double-clicked")]

    if name == "mouse_drag":
        sx, sy = int(args["start_x"]), int(args["start_y"])
        ex, ey = int(args["end_x"]), int(args["end_y"])
        validate_coords(sx, sy)
        validate_coords(ex, ey)
        duration = args.get("duration", 0.3)
        button = args.get("button", "left")
        pyautogui.moveTo(sx, sy, duration=0.1)
        pyautogui.drag(ex - sx, ey - sy, duration=duration, button=button)
        _time.sleep(0.2)
        return [TextContent(
            type="text", text=f"Dragged from ({sx},{sy}) to ({ex},{ey}) with {button} button"
        )]

    # ── Keyboard tools ──
    if name == "keyboard_type":
        text = args["text"]
        validate_text(text)
        interval = args.get("interval", TYPE_INTERVAL)
        # Arabic and non-Latin text: use clipboard paste (keystrokes don't work)
        if any(ord(c) > 127 for c in text):
            import pyperclip
            pyperclip.copy(text)
            _time.sleep(0.1)
            pyautogui.hotkey("ctrl", "v")
            _time.sleep(0.2)
            return [TextContent(
                type="text",
                text=f"Pasted {len(text)} characters via clipboard (non-Latin text)"
            )]
        # Latin text: type with human-like jitter per keystroke
        for ch in text:
            jitter = _random.uniform(-0.01, 0.01)
            actual_interval = max(0.005, interval + jitter)
            pyautogui.write(ch, interval=actual_interval)
        return [TextContent(
            type="text",
            text=f"Typed {len(text)} characters with human-like timing"
        )]

    if name == "keyboard_press":
        key = args["key"]
        pyautogui.press(key)
        _time.sleep(0.1)
        return [TextContent(type="text", text=f"Pressed key: {key}")]

    if name == "keyboard_hotkey":
        keys = args["keys"]
        pyautogui.hotkey(*keys)
        _time.sleep(0.2)
        return [TextContent(type="text", text=f"Pressed hotkey: {'+'.join(keys)}")]

    # ── Scroll ──
    if name == "scroll":
        amount = int(args["amount"])
        pyautogui.scroll(amount)
        return [TextContent(type="text", text=f"Scrolled {amount} clicks")]

    # ── Screenshot ──
    if name == "screenshot":
        img = pyautogui.screenshot()
        buf = io.BytesIO()
        # JPEG quality 85 for 5-10x smaller than PNG
        img.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return [
            ImageContent(
                type="image",
                data=b64,
                mimeType="image/jpeg",
            ),
            TextContent(
                type="text",
                text=f"Screenshot taken ({img.size[0]}x{img.size[1]}, "
                     f"{len(b64) // 1024} KB base64 JPEG)",
            ),
        ]

    # ── Screen size ──
    if name == "get_screen_size":
        w, h = pyautogui.size()
        return [TextContent(
            type="text",
            text=f"Screen size: {w}x{h}",
        )]

    # ── Wait ──
    if name == "wait":
        seconds = float(args["seconds"])
        await asyncio.sleep(seconds)
        return [TextContent(type="text", text=f"Waited {seconds}s")]

    # ── Locate on screen ──
    if name == "locate_on_screen":
        image_path = args["image_path"]
        if is_privacy_path(image_path):
            raise ValueError(f"Cannot search for images in privacy-protected path")
        confidence = args.get("confidence", 0.8)
        if not Path(image_path).exists():
            raise ValueError(f"Image not found: {image_path}")
        pos = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if pos:
            x, y, w, h = pos
            center_x, center_y = x + w // 2, y + h // 2
            return [TextContent(
                type="text",
                text=f"Found at ({x}, {y}) size ({w}x{h}). Center: ({center_x}, {center_y})",
            )]
        else:
            return [TextContent(type="text", text="Image not found on screen")]

    raise ValueError(f"Unknown tool: {name}")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN — stdio transport
# ═══════════════════════════════════════════════════════════════════════════

async def main():
    log(f"desktop_mcp_server.py starting — Screen: {SCREEN_W}x{SCREEN_H}")
    log(f"Python: {sys.version}")

    # Print startup info to stderr (stdout is reserved for MCP protocol)
    print(
        f"[desktop-mcp] Starting... Screen: {SCREEN_W}x{SCREEN_H}",
        file=sys.stderr,
    )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    if "--test" in sys.argv:
        # List all tools and exit (for verification)
        import json as _json
        tools = asyncio.run(list_tools())
        print(f"Desktop MCP Server — {len(tools)} tools")
        print(f"Screen: {SCREEN_W}x{SCREEN_H}")
        print()
        for t in tools:
            print(f"  {t.name:25s} — {t.description.split(chr(10))[0][:60]}")
        sys.exit(0)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("Server stopped by user")
        sys.exit(0)
