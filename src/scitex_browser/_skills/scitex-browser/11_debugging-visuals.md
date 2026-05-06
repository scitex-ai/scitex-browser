---
description: |
  [TOPIC] Debugging Visuals + Stepwise Capture
  [DETAILS] CSS/JS overlays for human-in-the-loop debugging, plus always-on screenshot+HTML capture (`capture_debug_artifacts_async`) at every interaction so post-mortem of selector regressions is mechanical, not guesswork.
tags: [scitex-browser-debugging-visuals]
---

# Debugging Visuals + Stepwise Capture

Two complementary debugging surfaces:

1. **Visual overlays** — CSS/JS injected into the page so a human can
   watch the automation drive. Best for interactive development.
2. **Stepwise capture** — screenshot + HTML written to disk at every
   click/fill (default). Best for post-mortem and for agent debugging
   without a live browser.

## Stepwise capture (always-on)

```python
from scitex_browser.debugging import capture_debug_artifacts_async

png, html = await capture_debug_artifacts_async(
    page,
    label="mfa_picker_before",        # short, filename-safe descriptor
    base_dir=None,                     # default: ~/.scitex/browser/cache/debug/
    full_page=True,
    include_html=True,
)
```

Writes:
- `<base_dir>/<label>_<ts>.png` — full-page screenshot
- `<base_dir>/<label>_<ts>.html` — `page.content()` snapshot

Failures are non-fatal (swallowed at debug log level). Returns
`(png_path, html_path)` or `(None, None)` if both fail.

**Why both image and HTML:** Screenshot shows what was rendered; HTML
shows the structure the locator was reasoning over. The pair makes
"the locator picked the wrong row" diagnosable in seconds.

### Auto-capture in click/fill helpers

`click_with_fallbacks_async(page, selector)` and
`fill_with_fallbacks_async(page, selector, value)` capture **before
+ after every call** by default. Opt out with `capture_debug=False`
in tight loops:

```python
await click_with_fallbacks_async(page, "#submit")
# → 2 PNG+HTML pairs: click_before_submit_*.{png,html} and click_after_submit_*.{png,html}
# → on failure: click_failed_submit_*.{png,html} instead

# Tight loop — opt out:
for sel in many_selectors:
    await click_with_fallbacks_async(page, sel, capture_debug=False)
```

### Per-package override

Pass `base_dir` to keep package artifacts in one folder:

```python
from pathlib import Path

await capture_debug_artifacts_async(
    page,
    label="sso_after_password",
    base_dir=Path.home() / ".scitex" / "scholar" / "cache" / "engine" / "screenshots",
)
```

## Visual overlays — interactive

Inject CSS/JS overlays into a Playwright page so humans can follow what
the automation is doing. Both sync and async variants are provided; the
async ones run in the event-loop-friendly Playwright API.

## One-time injection

```python
await inject_visual_effects_async(page)
```

Call once per page (or after navigation). All later `show_*` helpers
depend on the injected script.

## Cursor / click

* `show_cursor_at(page, x, y)` — render a visible cursor dot at viewport coordinates
* `show_click_effect(page, x, y)` — ripple animation at coordinates

## Step banners

* `show_step(page, "Login")` — top-of-page banner for current step
* `show_test_result(page, passed=True)` — final PASS/FAIL banner

## Grid + element highlight

* `show_grid_async(page, step=100)` — overlay a pixel grid (debug layout)
* `highlight_element_async(page, selector)` — outline a selector

## Console capture

```python
logs = setup_console_interceptor(page)
# ... run test ...
rich = collect_console_logs_detailed(page)
print(format_logs_devtools_style(rich))
```

## Failure artifacts

`save_failure_artifacts(page, out_dir)` dumps screenshot + full HTML +
console trace. `create_failure_capture_fixture(...)` is the pytest
plug-in form.
