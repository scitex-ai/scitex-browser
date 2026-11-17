---
description: |
  [TOPIC] Installation
  [DETAILS] Install the Python package and provide a compatible Playwright browser binary in the same environment.
tags: [scitex-browser-installation]
---

# Installation

The package requires Python 3.10 or newer (`pyproject.toml`). Its base
installation includes Playwright, Matplotlib and pytest; browser binaries
are separate from the Python wheel.

## Standard

```bash
pip install scitex-browser
python -m playwright install chromium       # download browser binaries
```

Run package installation and `python -m playwright` in the same Python
environment. Omit `chromium` to download all three Playwright engines.

A separate download is unnecessary when a compatible executable is already
available and explicitly selected by the caller. The owning offline control,
`.github/ci/probe-interactions.py --executable /absolute/browser/path`, verifies
that route using a caller-created Page; this is not automatic executable
discovery or a fallback to a different browser. Managed images retain their
own executable and runtime qualification requirements.

## Optional extras

| Extra | Install | Adds |
|-------|---------|------|
| dev   | `pip install scitex-browser[dev]` | build, coverage, async tests, scitex-dev |
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
python -m playwright install chromium
```
