---
description: |
  [TOPIC] Interaction
  [DETAILS] Interaction Helpers — see file body for details.
tags: [scitex-browser-interaction]
---

# Interaction Helpers

Resilient click/fill wrappers and popup dismissal, for flaky pages.

## Clicks with fallbacks

```python
from scitex_browser import click_with_fallbacks_async, click_center_async

await click_with_fallbacks_async(
    page,
    selectors=["button.submit", "text=Submit", "role=button[name=Submit]"],
)

# Click viewport-center of an element even if pointer-events are weird:
await click_center_async(page, "div.overlay")
```

`click_with_fallbacks_async` tries each selector in order; on each it
waits for visibility with a short timeout, then attempts a normal click,
then a JS click, then a force click. First success wins.

## Fills with fallbacks

```python
from scitex_browser import fill_with_fallbacks_async

await fill_with_fallbacks_async(
    page,
    selectors=["input[name=email]", "#email"],
    value="user@example.com",
)
```

## Popup handling

```python
from scitex_browser import PopupHandler, close_popups_async, ensure_no_popups_async

# One-shot helpers
await close_popups_async(page)
await ensure_no_popups_async(page)  # poll and close in a loop

# Long-lived handler attached to the page
handler = PopupHandler(page)
await handler.start()          # begin intercepting
# ... run test ...
await handler.stop()
```

`PopupHandler` registers a listener that auto-closes any new popup
windows for the lifetime of the page context.
