---
description: |
  [TOPIC] Installation
  [DETAILS] pip install scitex-browser. Brings Playwright; you must also run `playwright install` once to download Chromium/Firefox/WebKit binaries.
tags: [scitex-browser-installation]
---

# Installation

## Standard

```bash
pip install scitex-browser
playwright install chromium                 # required: browser binaries
```

`scitex-browser` wraps Playwright; the `playwright install` step is mandatory
the first time. Use `playwright install` (no arg) to fetch all three engines.

## Optional extras

| Extra      | Install                                       | Adds                              |
|------------|-----------------------------------------------|-----------------------------------|
| stealth    | `pip install scitex-browser[stealth]`         | playwright-stealth (anti-bot)     |
| zenrows    | `pip install scitex-browser[zenrows]` + key   | ZenRows residential proxy         |
| auth       | `pip install scitex-browser[auth]`            | OAuth + cookie-store helpers      |

## Verify

```bash
python -c "import scitex_browser; print(scitex_browser.__version__)"
python -c "from scitex_browser import save_as_pdf, SyncBrowserSession; print('ok')"
```

## Editable install (development)

```bash
git clone https://github.com/ywatanabe1989/scitex-browser
cd scitex-browser
pip install -e .
playwright install chromium
```
