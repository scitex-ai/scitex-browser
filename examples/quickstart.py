#!/usr/bin/env python3
"""Quickstart for scitex-browser: import + inspect public API offline.

This example does NOT launch a browser; it only verifies that the public
API is importable and exercises a couple of pure helpers.
"""

import scitex_browser
from scitex_browser import (
    SyncBrowserSession,
    format_logs_devtools_style,
    is_playwright_cli_available,
)


def main() -> int:
    public = [n for n in dir(scitex_browser) if not n.startswith("_")]
    print(f"scitex_browser public symbols ({len(public)}):")
    for name in public[:10]:
        print(f"  - {name}")
    print("  ...")

    print(f"\nplaywright CLI available: {is_playwright_cli_available()}")

    # format_logs_devtools_style is a pure function: feed it an empty list.
    formatted = format_logs_devtools_style([])
    print(f"format_logs_devtools_style([]) -> {formatted!r}")

    # SyncBrowserSession is a class; just confirm its qualname.
    print(f"SyncBrowserSession class: {SyncBrowserSession.__qualname__}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
