---
description: |
  [TOPIC] Quick Start
  [DETAILS] Quick Start — see file body for details.
tags: [scitex-browser-quick-start]
---

# Quick Start

## Save any page as PDF

```python
from scitex_browser import save_as_pdf_async

await save_as_pdf_async(page, "out.pdf")
```

Sync variant: `save_as_pdf(page, "out.pdf")`.

## Synchronous browser session with zombie-prevention

```python
from scitex_browser import sync_browser_session

with sync_browser_session(headless=False) as session:
    session.page.goto("https://example.org")
    session.page.click("a.more")
```

## Debug visuals (show cursor / click effect)

```python
from scitex_browser import (
    inject_visual_effects_async,
    show_cursor_at_async,
    show_click_effect_async,
)

await inject_visual_effects_async(page)
await show_cursor_at_async(page, 100, 200)
await show_click_effect_async(page, 100, 200)
```

## Popup / cookie handling

```python
from scitex_browser import ensure_no_popups_async, close_popups_async

await ensure_no_popups_async(page)
```

See [03_python-api.md](03_python-api.md) for the complete public API and
[14_auth-stealth-remote.md](14_auth-stealth-remote.md) for Google login
and ZenRows helpers.
