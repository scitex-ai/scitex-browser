# scitex-browser

Browser automation for scholarly paper access in the SciTeX ecosystem.

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
