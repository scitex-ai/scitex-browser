"""Exercise JavaScript fill on an owned offline page using a real browser."""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
import tempfile


async def verify(executable):
    from playwright.async_api import async_playwright
    import scitex_browser
    from scitex_browser import fill_with_fallbacks_async

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            executable_path=executable, args=["--no-sandbox"],
        )
        try:
            context = await browser.new_context()
            await context.route("**/*", lambda route: route.abort())
            page = await context.new_page()
            await page.set_content(
                '<input id="name"><script>'
                'window.observed=[];'
                'const input=document.querySelector("#name");'
                'for(const name of ["input","change"])'
                'input.addEventListener(name,()=>window.observed.push(name));'
                '</script>'
            )
            filled = await fill_with_fallbacks_async(
                page, "#name", "research", method="js", capture_debug=False,
            )
            observed = {
                "filled": filled,
                "value": await page.locator("#name").input_value(),
                "events": await page.evaluate("window.observed"),
            }
            assert observed == {
                "filled": True, "value": "research", "events": ["input", "change"],
            }, observed
            missing = await fill_with_fallbacks_async(
                page, "#absent", "research", method="js", capture_debug=False,
            )
            assert missing is False
            return {"browser": browser.version, "module": scitex_browser.__file__, "result": "passed", **observed}
        finally:
            await browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    if not args.executable.is_file() or not os.access(args.executable, os.X_OK):
        parser.error("--executable must identify an existing browser executable")
    with tempfile.TemporaryDirectory(prefix="scitex-browser-interaction-") as root:
        os.environ["SCITEX_DIR"] = str(Path(root) / "state")
        report = asyncio.run(verify(str(args.executable)))
        json.dump(report, sys.stdout)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
