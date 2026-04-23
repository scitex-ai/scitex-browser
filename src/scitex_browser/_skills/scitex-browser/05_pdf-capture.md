# PDF Capture

Save any page (including the built-in Chrome PDF viewer) to a local
PDF file.

## Regular HTML page

```python
from scitex_browser import save_as_pdf_async

await save_as_pdf_async(page, "article.pdf")
```

Sync wrapper: `save_as_pdf(page, "article.pdf")`.

Under the hood uses Playwright's `page.pdf(...)`; honors the current
viewport and emulated media.

## Chrome's built-in PDF viewer

Playwright cannot directly "print" a PDF the Chrome plugin is already
displaying. Use the two-step helpers:

```python
from scitex_browser import (
    detect_chrome_pdf_viewer_async,
    click_download_for_chrome_pdf_viewer_async,
)

if await detect_chrome_pdf_viewer_async(page):
    await click_download_for_chrome_pdf_viewer_async(page, out_dir="downloads/")
```

`click_download_*` locates the download button inside the PDF viewer
shadow DOM and intercepts the download event, writing the file to
`out_dir`.

## MCP entry point

`mcp__scitex__browser_save_as_pdf` wraps `save_as_pdf_async` for
skill/agent invocation. The Python API is the source of truth.
