#!/usr/bin/env python3
"""Unified GUI/CLI launcher.

With no arguments this opens the GUI. With arguments it preserves the existing
CLI route and behavior.
"""

from app import main


if __name__ == "__main__":
    raise SystemExit(main())
