"""Exercise PDF download coordinates and size guards on an owned offline page."""

import argparse
import asyncio
import json
import os
from pathlib import Path
import tempfile


async def verify(root, executable):
    from playwright.async_api import async_playwright
    from scitex_browser import click_download_for_chrome_pdf_viewer_async

    downloads = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=executable, headless=True)
        try:
            context = await browser.new_context(viewport={"width": 1000, "height": 800}, accept_downloads=True)
            await context.route("**/*", lambda route: route.abort())
            page = await context.new_page()
            for size in [1023, 1024, 1025]:
                await page.set_content('<a id="download" download="owned.pdf" '
                                       'style="position:fixed;left:940px;top:16px;width:30px;height:30px">Save</a>')
                await page.evaluate("""size => {
                    const data = new Uint8Array(size).fill(120);
                    document.querySelector('#download').href = URL.createObjectURL(new Blob([data], {type:'application/pdf'}));
                }""", size)
                output = root / ("download-" + str(size))
                ok = await click_download_for_chrome_pdf_viewer_async(page, output)
                saved = Path(str(output) + ".pdf")
                assert ok is (size > 1024) and saved.read_bytes() == b"x" * size, (size, ok)
                downloads.append({"bytes": size, "result": ok, "saved_bytes_identical": True})
            version = browser.version
        finally:
            await browser.close()
    return {"browser": version, "downloads": downloads}



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    if not args.executable.is_file() or not os.access(args.executable, os.X_OK):
        parser.error("--executable must identify an existing Chromium executable")
    import scitex_browser

    with tempfile.TemporaryDirectory(prefix="scitex-browser-pdf-download-") as directory:
        result = asyncio.run(verify(Path(directory), str(args.executable.resolve())))
        result["module"] = scitex_browser.__file__
        result["scope"] = "Owned blob downloads at expected coordinates; no printing, actual PDF viewer layout, PDF-content validity, live site or installation acceptance."
        print(json.dumps(result))


if __name__ == "__main__":
    main()
