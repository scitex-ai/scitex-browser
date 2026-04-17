---
name: scitex-browser
description: Playwright-based browser automation helpers for scholarly paper access — PDF capture, stealth, popup handling, test monitoring, Google OAuth, ZenRows remote browsing, and shared multi-agent sessions.
---

# scitex-browser

Playwright helper library used by SciTeX scholarly-paper pipelines. It does
not ship a CLI or MCP server — it is a Python library of async/sync utilities
that take an existing Playwright `Page` / `Browser` and add the behavior
needed to reach, render, download, and debug publisher web pages.

If the scenario is "I already have a Playwright page and need to X," this is
the right package. Greenfield web scraping without scholarly-paper context is
likely better served by raw Playwright.

## Install

```bash
pip install scitex-browser            # core (all deps optional)
pip install scitex-browser[playwright] # + playwright
pip install scitex-browser[dev]       # + pytest, pytest-cov
```

`playwright install chromium` is still required to fetch the browser binary.

## What actually ships (verified against the code)

### Top-level (`scitex_browser`)

All are re-exports — every attribute degrades to `None` if Playwright is not
installed, so `if save_as_pdf is None: ...` is a valid runtime guard.

- `is_playwright_cli_available()` — `bool`, checks for the `playwright-cli`
  npm binary on `PATH`.
- `save_as_pdf`, `save_as_pdf_async` — render the current page to PDF via
  Playwright's `page.pdf()`, after dismissing common consent banners.
- `detect_chrome_pdf_viewer_async`, `click_download_for_chrome_pdf_viewer_async`
  — detect Chrome's built-in PDF viewer (`<embed type="application/pdf">`)
  and trigger its download button.
- `click_center_async`, `click_with_fallbacks_async`,
  `fill_with_fallbacks_async` — click/fill with multiple selector/JS
  fallbacks when the straightforward path is flaky.
- `PopupHandler`, `close_popups_async`, `ensure_no_popups_async` — dismiss
  modal/consent popups.
- Visual debugging: `inject_visual_effects[_async]`, `show_cursor_at[_async]`,
  `show_click_effect[_async]`, `show_step[_async]`, `show_test_result[_async]`,
  `show_grid_async`, `highlight_element_async`.
- Failure capture: `setup_console_interceptor`, `collect_console_logs`,
  `collect_console_logs_detailed`, `format_logs_devtools_style`,
  `save_failure_artifacts`, `create_failure_capture_fixture`.
- `browser_logger` — module-level `BrowserLogger` singleton.
- Test monitoring: `TestMonitor`, `create_test_monitor_fixture`,
  `monitor_test` (periodic screenshots).
- Zombie prevention: `SyncBrowserSession`, `sync_browser_session`,
  `create_browser_session_fixture`.

### Subpackages

- `scitex_browser.auth` — `GoogleAuthHelper`, `google_login` (popup-based
  Google OAuth flow; reads `GOOGLE_EMAIL` / `GOOGLE_PASSWORD` env vars).
- `scitex_browser.automation` — `CookieAutoAcceptor` (per-page cookie banner
  handling).
- `scitex_browser.collaboration` — `SharedBrowserSession`, `SessionConfig`,
  `VisualFeedback`, `CredentialManager`. Marked `__experimental__ = True`;
  prints a load message to stdout.
- `scitex_browser.core` — `BrowserMixin` (mixin for async-context browser
  plumbing), `ChromeProfileManager` (pre-wired extension list: Zotero
  Connector, Lean Library, Pop-up Blocker, Accept-Cookies, 2Captcha, CAPTCHA
  Solver; manages persistent Chromium profiles under
  `$SCITEX_DIR/cache/chrome/<profile>`).
- `scitex_browser.debugging` — backs the top-level debugging exports.
- `scitex_browser.interaction` — backs the top-level interaction exports.
- `scitex_browser.pdf` — backs the top-level PDF exports.
- `scitex_browser.remote` — `ZenRowsAPIBrowser`,
  `ZenRowsRemoteScholarBrowserManager`, `CaptchaHandler` (CAPTCHA detection +
  manual/automated solve via installed solver extensions).
- `scitex_browser.stealth` — `StealthManager`, `HumanBehavior` (UA overrides,
  navigator property patches, randomized dwell/scroll).

### Compatibility shim

`scitex_browser._compat` exposes:
- `get_paths()` — returns scitex's path resolver if `scitex` is importable,
  else a local resolver rooted at `$SCITEX_DIR` (default `~/.scitex`).
- `ScholarError` — re-exported from `scitex.logging` if available, else a
  standalone `Exception` subclass.
- `get_scholar_config()` — returns `scitex.scholar.config.ScholarConfig()` if
  importable, else a minimal fallback exposing `get_cache_chrome_dir`.

## Typical usage

```python
import asyncio
from playwright.async_api import async_playwright
from scitex_browser import save_as_pdf_async, close_popups_async

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com/paper")
        await close_popups_async(page)
        await save_as_pdf_async(page, "paper.pdf")
        await browser.close()

asyncio.run(main())
```

```python
from scitex_browser.stealth import StealthManager

stealth = StealthManager()
await stealth.apply(context)  # patches UA + navigator before page.goto
```

```python
from scitex_browser.core import ChromeProfileManager

mgr = ChromeProfileManager("system")
if not mgr.check_extensions_installed():
    mgr.install_extensions_sync()
args = mgr.get_extension_args()  # for chromium.launch_persistent_context
```

## What this package does NOT do

- No CLI entrypoint. (`[project.scripts]` is empty.)
- No MCP server. The scitex ecosystem ships MCP servers in `scitex-orochi`
  and related packages, not here.
- No DOI → PDF pipeline. That lives in `scitex.scholar` (which imports from
  this package). This package is a helper layer.
- No paid third-party credentials are shipped; ZenRows + CAPTCHA solvers
  require your own keys and extension installs.

## Tests

161 unit tests under `tests/` cover auth, cookie handling, ChromeProfile
management, and the debugging modules. Many test files for
collaboration / pdf / stealth / interaction / remote are present as
placeholder stubs with commented-out legacy source — useful as context, not
as verification.

## Related

- `scitex` — umbrella scientific Python toolkit; this package was extracted
  from `scitex.browser`.
- `scitex.scholar` — scholarly-paper orchestration; the primary consumer.
- `scitex-orochi` — agent coordination / MCP surface for the fleet.
