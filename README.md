# scitex-browser

Playwright-based browser automation helpers for scholarly paper access,
extracted from the [SciTeX](https://github.com/ywatanabe1989/scitex)
ecosystem. A Python library — not a CLI, not an MCP server.

You bring the Playwright `Page` / `Browser` / `Context`; this package gives
you the behavior on top (consent-banner dismissal, PDF capture, stealth,
visual debugging, test monitoring, Google OAuth popup handling, ZenRows
remote rendering, persistent Chrome profiles with scholarly extensions
pre-wired).

## Install

```bash
pip install scitex-browser                # core (all deps optional)
pip install "scitex-browser[playwright]"  # + playwright
pip install "scitex-browser[dev]"         # + pytest, pytest-cov
```

Then, once:

```bash
playwright install chromium
```

## What's inside

| Subpackage                       | Notable exports |
|----------------------------------|-----------------|
| `scitex_browser` (top-level)     | `save_as_pdf[_async]`, `detect_chrome_pdf_viewer_async`, `click_with_fallbacks_async`, `fill_with_fallbacks_async`, `close_popups_async`, `PopupHandler`, `browser_logger`, `TestMonitor`, `SyncBrowserSession`, `is_playwright_cli_available` |
| `scitex_browser.auth`            | `GoogleAuthHelper`, `google_login` (popup-flow) |
| `scitex_browser.automation`      | `CookieAutoAcceptor` |
| `scitex_browser.collaboration`   | `SharedBrowserSession`, `SessionConfig`, `CredentialManager`, `VisualFeedback` (experimental) |
| `scitex_browser.core`            | `BrowserMixin`, `ChromeProfileManager` (Zotero, Lean Library, Pop-up Blocker, Accept-Cookies, 2Captcha/CAPTCHA Solver) |
| `scitex_browser.debugging`       | Console interception, failure artifact capture, periodic screenshots, visual cursor/grid overlays |
| `scitex_browser.interaction`     | Click/fill helpers with selector fallbacks, popup dismissal |
| `scitex_browser.pdf`             | Save page as PDF, detect + drive Chrome's built-in PDF viewer |
| `scitex_browser.remote`          | `ZenRowsAPIBrowser`, `ZenRowsRemoteScholarBrowserManager`, `CaptchaHandler` |
| `scitex_browser.stealth`         | `StealthManager`, `HumanBehavior` |

All Playwright-dependent imports are lazy; if Playwright isn't installed
the top-level names resolve to `None` so feature detection is a simple
`is None` check.

## Quick start

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

## Testing

```bash
pytest
```

161 tests across `tests/{auth,automation,core,debugging}` cover the core
Playwright-free logic. Test placeholders exist in other subdirectories and
are not counted toward the passing suite.

## Relationship to the SciTeX ecosystem

This package is one pip install of a larger toolkit. `scitex.scholar` is the
primary consumer — it orchestrates DOI → publisher → PDF pipelines on top of
these helpers. For agent coordination / MCP surfaces see `scitex-orochi`.

## License

AGPL-3.0. See [LICENSE](LICENSE).
