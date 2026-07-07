"""Standalone check that AnkiConnect is reachable (no MCP client needed).

Run with the project's venv Python:
    .venv\\Scripts\\python.exe scripts\\smoke_test.py

Exit code 0 = AnkiConnect answered; 1 = not reachable / error (the message
tells you what to fix).
"""

import sys
from pathlib import Path

# Allow running before `pip install -e .` by adding src/ to the path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from anki_mcp.anki_connect import AnkiError, invoke  # noqa: E402


def main() -> int:
    try:
        version = invoke("version")
        decks = invoke("deckNames")
    except AnkiError as exc:
        print(f"[FAIL] {exc}")
        return 1
    print(f"[OK] AnkiConnect version: {version}")
    print(f"[OK] {len(decks)} deck(s):")
    for name in decks:
        print(f"   - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
