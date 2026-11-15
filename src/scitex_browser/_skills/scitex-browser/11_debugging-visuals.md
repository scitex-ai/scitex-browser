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
    base_dir=None,                     # default: $SCITEX_DIR/browser/runtime/cache/debug/
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
from scitex_browser._state import cache_dir

# Use the canonical path resolver so SCITEX_DIR redirects are honoured.
await capture_debug_artifacts_async(
    page,
    label="sso_after_password",
    base_dir=cache_dir() / "engine" / "screenshots",
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
from scitex_browser.debugging import (
    setup_console_interceptor, collect_console_logs_detailed,
    format_logs_devtools_style,
)

setup_console_interceptor(page)
# ... run test ...
rich = collect_console_logs_detailed(page)
print(format_logs_devtools_style(rich))
```

Newly installed interceptors retain the newest 2,000 detailed entries and 500
simple strings across console calls, script/resource errors and unhandled
rejections. These are entry-count caps, not message-byte or total-memory limits.
`setup_console_interceptor` installs capture and returns `None`; repeated setup
on the same page preserves the existing interceptor and its records. It does
not upgrade an already installed older script in place.

The implementation is `debugging/_failure_capture.py`. Owning controls in
`tests/scitex_browser/debugging/test__failure_capture.py` execute the actual
interceptor JavaScript in an owned Node VM, checking boundaries, retained order,
entry schema and native-console forwarding. Live sites, message-size limits
and every browser engine require separate coverage.

## Failure artifacts — synchronous Page

Manual capture needs the page, a test name and an output directory:

```python
from scitex_browser.debugging import save_failure_artifacts

saved = save_failure_artifacts(
    page, test_name="login::submit", artifacts_dir="artifacts",
)
```

The helper writes into a timestamped subdirectory. The returned dictionary
contains `Path` values under `screenshot`, `console_logs` and `page_html` for
successful writes. Individual screenshot/log/HTML failures are caught, so the
result can be partial or empty; directory creation can still raise an error.
Console capture must have been installed before the events to retain them.
This helper uses a synchronous Playwright Page; `capture_debug_artifacts_async`
above is the separate async screenshot/HTML helper.

### Automatic capture with pytest

Put the following in `conftest.py`, alongside an existing synchronous `page`
fixture (for example, one supplied by your Playwright test configuration):

```python
from pathlib import Path
import pytest
from scitex_browser.debugging import create_failure_capture_fixture

capture_on_failure = create_failure_capture_fixture(
    Path(__file__).parent / "artifacts",
)

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
```

Both the fixture assignment and report hook are needed. The factory returns
an autouse fixture that installs console capture, yields to the test, then
saves artifacts when `request.node.rep_call.failed` is true. Without a report
hook that sets `rep_call`, it silently has no failure outcome to inspect.
This condition covers failures in the test call; it does not automatically
capture setup or teardown failures. Passing tests produce no failure artifacts.
Keep the page alive until this fixture finishes its teardown.

Implementation: [`debugging/_failure_capture.py`](../../debugging/_failure_capture.py).
The source checkout supplies a real offline browser/pytest probe:

```bash
python .github/ci/probe-failure-capture.py \
  --executable /existing/chromium --output /new/owned/artifact-directory
```

The probe checks manual screenshot/HTML/console output and actual pytest runs
with and without the report hook. Each child run intentionally has one passing
and one failing test; the probe checks that expected outcome rather than
claiming the child tests all pass. With the hook, only the failed call produces
all three artifacts; without it, neither does. It installs nothing and uses
owned pages with network blocked. Async Pages, setup/teardown failure capture,
live sites and installed-skill delivery need separate verification.
