#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-10-10 03:24:15 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex_repo/src/scitex/browser/interaction/click_with_fallbacks.py
# ----------------------------------------
from __future__ import annotations

import os

__FILE__ = "./src/scitex/browser/interaction/click_with_fallbacks.py"
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

import scitex_logging as logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


# 1. Main entry point
# ---------------------------------------
async def click_with_fallbacks_async(
    page: Page,
    selector: str,
    method: str = "auto",
    verbose: bool = False,
    capture_debug: bool = True,
) -> bool:
    """Click element using multiple fallback methods.

    Args:
        page: Playwright page object
        selector: CSS selector for the element
        method: Click method ("auto", "playwright", "force", "js")
        verbose: Enable visual feedback via popup system (default False)
        capture_debug: Save screenshot+HTML before/after the click
            (default True). Disabled in tight loops or hot paths
            where artifact volume hurts.

    Returns:
        bool: True if click successful, False otherwise
    """
    from ..debugging import browser_logger
    from ..debugging._capture_debug import capture_debug_artifacts_async

    if method == "auto":
        methods_order = ["playwright", "force", "js"]
    else:
        methods_order = [method]

    methods = {
        "playwright": _click_with_playwright,
        "force": _click_with_force,
        "js": _click_with_js,
    }

    if verbose:
        await browser_logger.debug(
            page, f"Attempting click: {selector}", verbose=verbose
        )

    label_base = _safe_label_from_selector(selector)
    if capture_debug:
        await capture_debug_artifacts_async(page, label=f"click_before_{label_base}")

    for method_name in methods_order:
        if method_name in methods:
            success = await methods[method_name](page, selector)
            if success:
                logger.debug(f"Click successful with {method_name}: {selector}")
                if verbose:
                    await browser_logger.debug(
                        page,
                        f"✓ Click successful ({method_name}): {selector}",
                        verbose=verbose,
                    )
                if capture_debug:
                    await capture_debug_artifacts_async(
                        page, label=f"click_after_{label_base}"
                    )
                return True

    logger.error(f"All click methods failed for {selector}")
    if verbose:
        await browser_logger.debug(
            page, f"✗ All click methods failed: {selector}", verbose=verbose
        )
    if capture_debug:
        await capture_debug_artifacts_async(page, label=f"click_failed_{label_base}")
    return False


def _safe_label_from_selector(selector: str, max_len: int = 40) -> str:
    """Selector → filename-safe short label."""
    out = "".join(c if c.isalnum() else "_" for c in selector)
    out = out.strip("_")
    while "__" in out:
        out = out.replace("__", "_")
    return out[:max_len] or "unnamed"


# 2. Helper functions
# ---------------------------------------
async def _click_with_playwright(page: Page, selector: str) -> bool:
    try:
        await page.click(selector, timeout=5000)
        return True
    except Exception:
        return False


async def _click_with_force(page: Page, selector: str) -> bool:
    try:
        await page.click(selector, force=True, timeout=5000)
        return True
    except Exception:
        return False


async def _click_with_js(page: Page, selector: str) -> bool:
    try:
        result = await page.evaluate(
            """(selector) => {
                const element = document.querySelector(selector);
                if (element) {
                    element.click();
                    return 'success';
                }
                return 'element not found';
            }""",
            selector,
        )
        return result == "success"
    except Exception:
        return False


def main(args):
    """Demonstrate click_with_fallbacks functionality."""
    import asyncio

    from playwright.async_api import async_playwright

    from ..debugging import browser_logger

    async def demo():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            await browser_logger.debug(
                page, "Click with Fallbacks: Starting demo", verbose=True
            )

            # Navigate to a test page
            await page.goto("https://example.com", timeout=30000)

            # Demonstrate clicking with verbose feedback
            await browser_logger.debug(
                page, "Testing click with fallbacks...", verbose=True
            )

            # Try to click a common element
            success = await click_with_fallbacks_async(
                page,
                "a",
                verbose=True,  # Click first link
            )

            if success:
                logger.success("Click demonstration completed successfully")
            else:
                logger.warning("Click demonstration: no clickable element found")

            await browser_logger.debug(page, "✓ Demo complete", verbose=True)

            await asyncio.sleep(2)
            await browser.close()

    asyncio.run(demo())
    return 0


def parse_args():
    """Parse command line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Click with fallbacks demo")
    return parser.parse_args()


def run_main() -> None:
    """Initialize scitex framework, run main function, and cleanup."""
    global CONFIG, CC, sys, plt, rng

    import sys

    import matplotlib.pyplot as plt
    import scitex as stx

    args = parse_args()

    CONFIG, sys.stdout, sys.stderr, plt, CC, rng = stx.session.start(
        sys,
        plt,
        args=args,
        file=__FILE__,
        sdir_suffix=None,
        verbose=False,
        agg=True,
    )

    exit_status = main(args)

    stx.session.close(
        CONFIG,
        verbose=False,
        notify=False,
        message="",
        exit_status=exit_status,
    )


if __name__ == "__main__":
    run_main()

# python -m scitex_browser.interaction.click_with_fallbacks

# EOF
