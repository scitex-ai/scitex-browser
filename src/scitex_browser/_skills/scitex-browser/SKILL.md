---
name: scitex-browser
description: |
  [WHAT] Playwright wrappers for scientific web scraping + AI-agent browsing — adds debugging visuals (cursor/click overlays, step markers, grid), popup/cookie handling, PDF capture (including the notoriously-hidden Chrome PDF viewer), resilient click/fill with selector fallbacks, test-monitor fixtures, and browser-session management. Public API (~36 symbols) — sessions (`SyncBrowserSession`…
  [WHEN] Use whenever the user asks to "save a webpage as PDF", "download from Chrome's PDF viewer", "click this element with fallback selectors", "handle GDPR/cookie popups", "add cursor/click overlays for debug video", "collect browser console logs DevTools-style", "wrap a test with a browser-session fixture", "set up failure-artifact capture", or mentions `scitex.
  [HOW] browser`, Playwright for scientific scraping, AI-agent browser automation.
tags: [scitex-browser]
primary_interface: python
interfaces:
  python: 3
  cli: 0
  mcp: 0
  skills: 2
  http: 0
---

# scitex-browser

> **Interfaces:** Python ⭐⭐⭐ (primary) · CLI — · MCP — · Skills ⭐⭐ · Hook — · HTTP —

Thin, categorized wrappers around Playwright. Grouped into sub-packages;
each one is a flat import surface re-exported from the top-level
`scitex_browser` namespace.

## Installation & import (two equivalent paths)

The same module is reachable via two install paths. Both forms work at
runtime; which one a user has depends on their install choice.

```python
# Standalone — pip install scitex-browser
import scitex_browser
scitex_browser.save_as_pdf(...)

# Umbrella — pip install scitex
import scitex.browser
scitex.browser.save_as_pdf(...)
```

`pip install scitex-browser` alone does NOT expose the `scitex` namespace;
`import scitex.browser` raises `ModuleNotFoundError`. To use the
`scitex.browser` form, also `pip install scitex`.

See [../../general/02_interface-python-api.md] for the ecosystem-wide
rule and empirical verification table.

## Sub-skills

### Core

* [01_installation](01_installation.md) — pip install + `playwright install`
* [02_quick-start](02_quick-start.md) — Minimal save-as-pdf / session / visuals
* [03_python-api](03_python-api.md) — Public symbols grouped by sub-package
* [10_session-lifecycle](10_session-lifecycle.md) — Sync/shared sessions, fixtures

### Sub-packages

* [11_debugging-visuals](11_debugging-visuals.md) — Cursor/click/step overlays, console logs
* [12_pdf-capture](12_pdf-capture.md) — `save_as_pdf`, Chrome PDF viewer
* [13_interaction](13_interaction.md) — Resilient click/fill, popup handling
* [14_auth-stealth-remote](14_auth-stealth-remote.md) — OAuth, stealth, ZenRows, CAPTCHA


## Environment

- [20_env-vars.md](20_env-vars.md) — SCITEX_* env vars read by scitex-browser at runtime
