# scitex-browser

Browser automation for scholarly paper access in the SciTeX ecosystem.

> **Interfaces:** Python ⭐⭐⭐ (primary) · CLI — · MCP — · Skills ⭐⭐ · Hook — · HTTP —

## Problem and Solution


| # | Problem | Solution |
|---|---------|----------|
| 1 | **Playwright is great but verbose** -- every scraping script reinvents popup dismissal, retry logic, Chrome-PDF-viewer workaround | **Helpers**: `click_with_fallbacks_async([sel1, sel2])`, `save_as_pdf_async`, `close_popups_async`, `inject_visual_effects` — focused wrappers around Playwright |
| 2 | **Tests fail silently with no artifact** -- `pytest-playwright` doesn't auto-capture screen + DOM on failure | **`TestMonitor` + `create_failure_capture_fixture`** -- captures screenshot + page HTML + console log on every failure |

## Features

- **Debugging**: Visual cursor feedback, popup logging, failure capture, test monitoring
- **PDF**: Chrome PDF viewer detection, save-as-PDF automation
- **Interaction**: Click/fill with fallbacks, popup handling
- **Stealth**: Human-like behavior simulation, stealth browser management
- **Remote**: ZenRows API integration, CAPTCHA handling
- **Collaboration**: Shared browser sessions, credential management
- **Auth**: Google authentication helpers

## Installation

```bash
pip install scitex-browser
```

### Optional extras

```bash
pip install scitex-browser[stealth]   # playwright-stealth
pip install scitex-browser[remote]    # ZenRows integration
pip install scitex-browser[scitex]    # Full SciTeX integration
```

## Quick start

```python
from scitex_browser import save_as_pdf, browser_logger
from scitex_browser.stealth import StealthManager
```

## License

AGPL-3.0. See [LICENSE](LICENSE) for details.
