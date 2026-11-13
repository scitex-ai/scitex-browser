---
description: |
  [TOPIC] Interaction
  [DETAILS] Interaction Helpers — see file body for details.
tags: [scitex-browser-interaction]
---

# Interaction Helpers

Use an existing asynchronous Playwright Page. Click and fill helpers accept
one CSS selector string and try alternative interaction methods for that selector.

## Clicks with fallbacks

```python
from scitex_browser import click_with_fallbacks_async, click_center_async

clicked = await click_with_fallbacks_async(page, selector="button.submit")

# Click the center of the viewport.
await click_center_async(page)
```

With `method="auto"`, clicking tries Playwright, a forced Playwright click,
then JavaScript. It returns `True` after the first method completes successfully,
or `False` when all methods fail.

## Fills with fallbacks

```python
from scitex_browser import fill_with_fallbacks_async

filled = await fill_with_fallbacks_async(
    page, selector="input[name=email]", value="reader@example.invalid",
)
```

Automatic filling tries Playwright fill, click/select-all/type, then JavaScript.
It returns a boolean result. Both click and fill save screenshots and HTML
around the operation by default. Set `capture_debug=False` to disable those artifacts.
See [debug capture](11_debugging-visuals.md) for artifact locations and options.

## Popup handling

Popup handling uses explicit calls to inspect supported in-page cookie banners
and overlays. The convenience helpers return the handled count and records,
or whether the page is clear.

```python
from scitex_browser import PopupHandler, close_popups_async, ensure_no_popups_async

handled, records = await close_popups_async(page, wait_first=False)
clear = await ensure_no_popups_async(page)

handler = PopupHandler(page)
handled = await handler.handle_all_popups()
handled = await handler.wait_and_handle_popups(timeout_ms=5000)
```

Use `handle_all_popups()` to inspect and handle the current page, or
`wait_and_handle_popups()` to poll for a popup within a requested wait period.

## Source and verification

The implementations are
[click](../../interaction/click_with_fallbacks.py),
[fill](../../interaction/fill_with_fallbacks.py), and
[popup handling](../../interaction/close_popups.py).
The source checkout includes an offline real-browser probe for JavaScript fill,
its input/change events and the missing-selector result. Supply an existing
Chromium-compatible executable:

```bash
python .github/ci/probe-interactions.py --executable /path/to/chromium
```

The probe owns its page and temporary state. It does not check live sites,
authentication flows or every popup pattern.
