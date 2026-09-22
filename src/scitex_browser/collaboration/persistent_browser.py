#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-10-19 05:55:00 (ywatanabe)"
# File: ./src/scitex/browser/collaboration/persistent_browser.py
# ----------------------------------------
"""
Persistent Browser - Keep open forever, attach/detach anytime.

This is the key to true AI-human collaboration!

Usage:
    # Terminal 1: Start browser server (once)
    python3 -m scitex_browser.collaboration.server

    # Terminal 2+: AI agents attach
    session = await SharedBrowserSession.attach()
    await session.navigate("...")
    # Script ends, browser stays open!

    # You (human): See everything in browser window, can interact!
"""

import scitex_logging as logging
logger = logging.getLogger(__name__)


import asyncio
import signal
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from scitex_browser._state import persistent_dir


class PersistentBrowserServer:
    """
    Browser server that stays running.

    Keeps browser open, allows scripts to attach/detach.
    """

    def __init__(
        self,
        port: int = 9222,
        session_dir: Optional[str] = None,
        browser_type: str = "chromium",
        headless: bool = False,
    ):
        self.port = port
        self.browser_type = browser_type
        self.headless = headless

        # Session directory under the package's own runtime tree.
        # Defaults to $SCITEX_DIR/browser/runtime/persistent/.
        if session_dir:
            self.session_dir = session_dir
        else:
            self.session_dir = str(persistent_dir())

        self.playwright = None
        self.context = None
        self.running = False

    async def start(self):
        """
        Start persistent browser server.

        Browser stays open until explicitly stopped.
        """
        logger.info("=" * 60)
        logger.info("🌐 Starting Persistent Browser Server")
        logger.info("=" * 60)

        self.playwright = await async_playwright().start()

        # Launch persistent context with remote debugging
        browser_launcher = getattr(self.playwright, self.browser_type)

        self.context = await browser_launcher.launch_persistent_context(
            user_data_dir=self.session_dir,
            headless=self.headless,
            args=[
                f"--remote-debugging-port={self.port}",
                "--disable-blink-features=AutomationControlled",
            ],
            viewport={"width": 1920, "height": 1080},
        )

        # Create initial page
        if not self.context.pages:
            page = await self.context.new_page()
            await page.goto("about:blank")

        self.running = True

        logger.info(f"\n✅ Browser server started!")
        logger.info(f"   Port: {self.port}")
        logger.info(f"   CDP URL: http://localhost:{self.port}")
        logger.info(f"   Session dir: {self.session_dir}")
        logger.info(f"   Headless: {self.headless}")
        logger.info(f"\n💡 Scripts can now attach to this browser!")
        logger.info(f"   Chrome DevTools: chrome://inspect")
        logger.info(f"\n⏸️  Press Ctrl+C to stop the browser server")
        logger.info("=" * 60 + "\n")

        # Handle shutdown gracefully
        loop = asyncio.get_event_loop()

        def handle_signal(sig, frame):
            logger.info("\n\n🛑 Shutting down browser server...")
            self.running = False

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Keep running
        try:
            while self.running:
                await asyncio.sleep(1)
        finally:
            await self.stop()

    async def stop(self):
        """Stop browser server."""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()

        logger.info("\n✅ Browser server stopped")


async def attach_to_browser(cdp_url: str = "http://localhost:9222") -> Page:
    """
    Attach to running persistent browser.

    Returns:
        Page instance from the persistent browser

    Example:
        page = await attach_to_browser()
        await page.goto("https://example.com")
        # Script ends, browser stays open!
    """
    playwright = await async_playwright().start()

    try:
        # Connect via Chrome DevTools Protocol
        browser = await playwright.chromium.connect_over_cdp(cdp_url)

        # Get context
        contexts = browser.contexts
        if not contexts:
            raise RuntimeError("No browser context available")

        context = contexts[0]

        # Get or create page
        pages = context.pages
        if pages:
            page = pages[0]
        else:
            page = await context.new_page()

        logger.info(f"✅ Attached to browser at {cdp_url}")
        return page

    except Exception as e:
        await playwright.stop()
        raise RuntimeError(f"Failed to attach to browser: {e}")


# EOF
