---
name: scitex-browser
description: Playwright helpers for scientific scraping — debugging visuals, popup/cookie handling, PDF capture, stealth, remote CAPTCHA, and multi-agent collaboration. Use when automating a browser in a research workflow.
---

# scitex-browser

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

* [01_quick-start](01_quick-start.md) — Minimal save-as-pdf / session / visuals
* [02_python-api](02_python-api.md) — Public symbols grouped by sub-package
* [03_session-lifecycle](03_session-lifecycle.md) — Sync/shared sessions, fixtures

### Sub-packages

* [04_debugging-visuals](04_debugging-visuals.md) — Cursor/click/step overlays, console logs
* [05_pdf-capture](05_pdf-capture.md) — `save_as_pdf`, Chrome PDF viewer
* [06_interaction](06_interaction.md) — Resilient click/fill, popup handling
* [07_auth-stealth-remote](07_auth-stealth-remote.md) — OAuth, stealth, ZenRows, CAPTCHA
