---
description: |
  [TOPIC] PDF Capture
  [DETAILS] URL-to-PDF printing and coordinate-based downloads from an existing Chrome PDF viewer, with separate return values and verification scope.
tags: [scitex-browser-pdf-capture]
---

# PDF Capture

Choose between printing a URL in a new headless Chromium browser and downloading
from a PDF viewer already open in an asynchronous Playwright Page.

## Print an HTML URL

```python
from scitex_browser import save_as_pdf_async

pdf_path = await save_as_pdf_async(
    "https://example.org/article", "article.pdf", wait_seconds=3,
)
```

The first argument is a **URL string**. The helper creates its own browser and
page; it does not reuse an existing page, its authentication or viewport.
Use `file:///absolute/path/article.html` for a local HTML file. A URL without
`http://`, `https://` or `file://` is prefixed with `https://`.

The helper navigates with `wait_until="networkidle"` and a 60-second navigation
timeout, then waits `wait_seconds` (default 3). Before printing it tries common
consent/close buttons and removes large fixed/sticky overlays, so the printout
can differ from the original page. These heuristics require checking on the
intended site.

Printing uses `page.pdf(...)`: A4, background graphics enabled and 10mm margins
by default. Set `format`, `print_background`, `margin_top`, `margin_bottom`,
`margin_left` and `margin_right` as needed. No viewport or media option is exposed
by this wrapper.

The output parent directory is created, a non-PDF suffix is replaced with `.pdf`,
and success returns the absolute output path as a string. Missing output or an
output smaller than 1,024 bytes raises `RuntimeError`; this size guard does not
validate PDF contents. Other navigation or browser errors can also propagate.

The synchronous wrapper has the same URL/output arguments:

```python
from scitex_browser import save_as_pdf

pdf_path = save_as_pdf("https://example.org/article", "article.pdf")
```

It uses `asyncio.run`; use the async function inside an existing event loop.
Chromium and Playwright must already be available in the calling environment.

## Download from an existing Chrome PDF viewer

```python
from pathlib import Path
from scitex_browser import (
    detect_chrome_pdf_viewer_async,
    click_download_for_chrome_pdf_viewer_async,
)

# page is an existing asynchronous Page; the caller waits for it to load.
await page.wait_for_load_state("networkidle")
if await detect_chrome_pdf_viewer_async(page):
    Path("downloads").mkdir(exist_ok=True)
    downloaded = await click_download_for_chrome_pdf_viewer_async(
        page, output_path="downloads/article.pdf",
    )
```

Detection is heuristic: it checks embeds, frames, viewer-related DOM markers,
content type and the browser's PDF MIME plugin. A positive result does not
prove a viewer is open or its download control is usable.

Downloading clicks viewport coordinates at 95% width and 3% height; it does
not locate a shadow-DOM button. It requires a usable `page.viewport_size` and
a viewer layout with the download control at those coordinates. It waits up
to 120 seconds for the download event, awaits the download's temporary path,
pauses two seconds, then saves to the supplied **file path**. There is no separate
10-second completion timeout in this helper. The caller creates parent folders.
If the path does not end in lowercase `.pdf`, `.pdf` is appended.

The result is `True` when the saved file exists and is larger than 1,024 bytes;
otherwise it is `False`. Exceptions inside the helper are logged and return
`False`. This is a size check, not PDF parsing or a guarantee for every viewer.

## Ownership and verification

Printing is implemented in [`pdf/_save_as_pdf.py`](../../pdf/_save_as_pdf.py).
Downloading is implemented in
[`pdf/click_download_for_chrome_pdf_viewer.py`](../../pdf/click_download_for_chrome_pdf_viewer.py).
The owning tests in `tests/scitex_browser/pdf/` currently check imports only.

For download behavior, the source checkout supplies an explicit offline probe:

```bash
python .github/ci/probe-pdf-download.py --executable /existing/chromium
```

This requires existing Playwright and a Chromium-compatible executable; it
installs nothing. It checks the download helper using real blob downloads at
the expected coordinates and the 1,023/1,024/1,025-byte boundary. These blobs
check saving and size guards, not valid PDF contents or Chrome's actual
PDF-viewer layout.

Printing, URL normalization and other print options/error paths described above
need separate behavioral coverage with a compatible Playwright browser. Import
smoke tests or a passing download probe do not establish rendered PDF output.
Live/authenticated sites, every viewer/browser and browser installation also
require separate checks.

These are the leaf package's Python APIs. An umbrella MCP tool name or live
host route must be verified in the interface that supplies it; this guide does
not establish one from a Python export alone.
