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

| Extra | Install | Adds |
|-------|---------|------|
| dev   | `pip install scitex-browser[dev]` | pytest, scitex-dev |
| docs  | `pip install scitex-browser[docs]` | Sphinx, RTD theme |
| all   | `pip install scitex-browser[all]` | dev + docs |

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
