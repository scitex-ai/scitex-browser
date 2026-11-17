import asyncio

import pytest

from scitex_browser import click_center_async


def test_module_importable_mod_is_not_none():
    """Smoke test: parent module imports without error."""
    # Arrange
    import importlib
    # Act
    mod = importlib.import_module("scitex_browser.interaction")
    # Assert
    assert mod is not None


class _CenterMouse:
    def __init__(self):
        self.calls = []
        self.result = object()

    async def click(self, x, y):
        self.calls.append((x, y))
        return self.result


class _CenterPage:
    def __init__(self, viewport, live):
        self.viewport_size = viewport
        self.live = live
        self.mouse = _CenterMouse()
        self.evaluations = 0
        self.waits = []
        self.error = None

    async def evaluate(self, script):
        self.evaluations += 1
        if self.error is not None:
            raise self.error
        return dict(self.live)

    async def wait_for_timeout(self, delay):
        self.waits.append(delay)


@pytest.mark.parametrize("viewport,live,center,evaluations", [
    ({"width": 800, "height": 600}, None, (400, 300), 0),
    ({"width": 801, "height": 601}, None, (400, 300), 0),
    (None, {"width": 800, "height": 600}, (400, 300), 1),
    (None, {"width": 801, "height": 601}, (400, 300), 1),
    (None, {"width": 1, "height": 1}, (0, 0), 1),
])
def test_center_uses_configured_or_live_viewport(viewport, live, center, evaluations):
    # Arrange
    page = _CenterPage(viewport, live)
    # Act
    result = asyncio.run(click_center_async(page))
    # Assert
    assert (page.mouse.calls, page.evaluations, page.waits, result is page.mouse.result) == (
        [center], evaluations, [1000], True,
    )


def test_live_viewport_is_measured_again_for_each_click():
    # Arrange
    page = _CenterPage(None, {"width": 800, "height": 600})
    # Act
    asyncio.run(click_center_async(page))
    page.live = {"width": 1001, "height": 701}
    asyncio.run(click_center_async(page))
    # Assert
    assert (page.mouse.calls, page.evaluations, page.waits) == (
        [(400, 300), (500, 350)], 2, [1000, 1000],
    )


def test_live_viewport_error_propagates_before_any_click():
    # Arrange
    page = _CenterPage(None, None)
    page.error = RuntimeError("owned page unavailable")
    caught = None
    # Act
    try:
        asyncio.run(click_center_async(page))
    except Exception as error:
        caught = error
    # Assert
    assert (caught is page.error, page.mouse.calls, page.waits) == (True, [], [])




if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/browser/interaction/click_center.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # Timestamp: "2025-10-10 03:24:17 (ywatanabe)"
# # File: /home/ywatanabe/proj/scitex_repo/src/scitex/browser/interaction/click_center.py
# # ----------------------------------------
# from __future__ import annotations
# import os
#
# __FILE__ = "./src/scitex/browser/interaction/click_center.py"
# __DIR__ = os.path.dirname(__FILE__)
# # ----------------------------------------
#
# __FILE__ = __file__
#
# """
# Click center of viewport utility for browser automation.
#
# Functionalities:
#   - Clicks the center point of the browser viewport
#   - Provides visual feedback during operation
#   - Simple utility for centering interactions
#
# Dependencies:
#   - packages:
#     - playwright
#
# IO:
#   - input-files: None
#   - output-files: None
# """
#
# """Imports"""
# from scitex import logging
#
# logger = logging.getLogger(__name__)
#
# """Functions & Classes"""
#
#
# async def click_center_async(
#     page, verbose: bool = False, func_name="click_center_async"
# ):
#     """Click the center of the viewport.
#
#     Args:
#         page: Playwright page object
#         verbose: Enable visual feedback (default False)
#
#     Returns:
#         Click result
#     """
#     from ..debugging import browser_logger
#
#     if verbose:
#         await browser_logger.debug(
#             page,
#             f"{func_name}: Clicking the center of the page...",
#             verbose=verbose,
#         )
#
#     viewport_size = page.viewport_size
#     center_x = viewport_size["width"] // 2
#     center_y = viewport_size["height"] // 2
#     clicked = await page.mouse.click(center_x, center_y)
#     await page.wait_for_timeout(1_000)
#
#     logger.debug(f"{func_name}: Clicked center at ({center_x}, {center_y})")
#     return clicked
#
#
# def main(args):
#     """Demonstrate click_center functionality."""
#     import asyncio
#
#     from playwright.async_api import async_playwright
#
#     from ..debugging import browser_logger
#
#     async def demo():
#         async with async_playwright() as p:
#             browser = await p.chromium.launch(headless=False)
#             page = await browser.new_page()
#
#             await browser_logger.debug(
#                 page, "Click Center: Starting demo", verbose=True
#             )
#
#             await page.goto("https://example.com", timeout=30000)
#
#             # Demonstrate clicking center
#             await click_center_async(page, verbose=True)
#
#             logger.success("Click center demonstration complete")
#
#             await browser_logger.debug(page, "✓ Demo complete", verbose=True)
#
#             await asyncio.sleep(2)
#             await browser.close()
#
#     asyncio.run(demo())
#     return 0
#
#
# def parse_args():
#     """Parse command line arguments."""
#     import argparse
#
#     parser = argparse.ArgumentParser(description="Click center demo")
#     return parser.parse_args()
#
#
# def run_main() -> None:
#     """Initialize scitex framework, run main function, and cleanup."""
#     global CONFIG, CC, sys, plt, rng
#
#     import sys
#
#     import matplotlib.pyplot as plt
#
#     import scitex as stx
#
#     args = parse_args()
#
#     CONFIG, sys.stdout, sys.stderr, plt, CC, rng = stx.session.start(
#         sys,
#         plt,
#         args=args,
#         file=__FILE__,
#         sdir_suffix=None,
#         verbose=False,
#         agg=True,
#     )
#
#     exit_status = main(args)
#
#     stx.session.close(
#         CONFIG,
#         verbose=False,
#         notify=False,
#         message="",
#         exit_status=exit_status,
#     )
#
#
# if __name__ == "__main__":
#     run_main()
#
# # python -m scitex.browser.interaction.click_center
#
# # EOF

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/browser/interaction/click_center.py
# --------------------------------------------------------------------------------
