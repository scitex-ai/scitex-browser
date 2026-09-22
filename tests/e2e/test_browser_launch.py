"""End-to-end: real headless Chromium against a loopback-only data: URL.

Gated by ``RUN_E2E=1`` (skipped by default, including plain ``pytest``
runs and CI). No network access: the page under test is a ``data:``
URL, so the only real subsystem exercised is the locally installed
Chromium binary driven through the package's pinned ``playwright``
dependency.
"""

import os

import pytest

pytestmark = pytest.mark.e2e


@pytest.mark.skipif(
    os.environ.get("RUN_E2E") != "1",
    reason="e2e needs RUN_E2E=1 (real Chromium launch)",
)
def test_headless_chromium_renders_data_url():
    # Arrange
    from playwright.sync_api import sync_playwright

    # Act
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("data:text/html,<title>scitex-e2e</title><h1>hi</h1>")
        title = page.title()
        browser.close()
    # Assert
    assert title == "scitex-e2e"
