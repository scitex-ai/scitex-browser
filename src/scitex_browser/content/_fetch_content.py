#!/usr/bin/env python3
"""Capture a Chrome-rendered page as HTML or plain text.

This is the counterpart to :mod:`scitex_browser.pdf`. PDF is the right output
when the *layout* is the artifact; HTML/text is the right output when the
*data* is. Sites that block plain HTTP clients (``requests`` gets a 403) still
serve a real browser, so this is the supported way to feed such pages into an
HTML parser such as ``scitex_web``.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from .._page_prep import dismiss_overlays_async, normalize_url

# Reads the rendered, user-visible text rather than the raw markup.
_INNER_TEXT_JS = "() => document.body ? document.body.innerText : ''"

_DEFAULT_NAV_TIMEOUT_MS = 60_000


@asynccontextmanager
async def _chromium_page(url: str, *, wait_until: str, timeout_ms: int):
    """Yield a headless-Chromium page already navigated to ``url``.

    This is the default ``open_page`` for :func:`fetch_content_async`; tests
    substitute their own so the extraction logic runs without a browser.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            yield page
        finally:
            await browser.close()


async def extract_from_page_async(
    page,
    *,
    dismiss_overlays: bool = False,
    selector: str | None = None,
) -> dict:
    """Read content out of an already-navigated page.

    Parameters
    ----------
    page
        Playwright page object, already navigated.
    dismiss_overlays : bool
        Clear cookie banners and large sticky overlays before reading. Off by
        default: the overlay sweep removes any large fixed/sticky element,
        which can delete real content on sites that render results inside one.
    selector : str or None
        When given, read only the first element matching this CSS selector
        instead of the whole document. Raises if it matches nothing.

    Returns
    -------
    dict
        ``{"url": final URL after redirects, "title": page title,
        "html": markup, "text": visible text}``.
    """
    if dismiss_overlays:
        await dismiss_overlays_async(page)

    if selector is None:
        html = await page.content()
        text = await page.evaluate(_INNER_TEXT_JS)
    else:
        element = page.locator(selector).first
        if await element.count() == 0:
            raise ValueError(f"selector matched no element: {selector!r}")
        html = await element.inner_html()
        text = await element.inner_text()

    return {
        "url": page.url,
        "title": await page.title(),
        "html": html,
        "text": text,
    }


async def fetch_content_async(
    url: str,
    *,
    wait_seconds: float = 3,
    wait_until: str = "networkidle",
    timeout_ms: int = _DEFAULT_NAV_TIMEOUT_MS,
    dismiss_overlays: bool = False,
    selector: str | None = None,
    cdp_url: str | None = None,
    open_page=None,
) -> dict:
    """Navigate to ``url`` and return its rendered content.

    Parameters
    ----------
    url : str
        URL to capture. A missing scheme is filled in as ``https://``.
    wait_seconds : float
        Extra seconds to wait after page load, for JS that renders late.
    wait_until : str
        Playwright load state to navigate against.
    timeout_ms : int
        Navigation timeout in milliseconds.
    dismiss_overlays : bool
        See :func:`extract_from_page_async`.
    selector : str or None
        See :func:`extract_from_page_async`.
    cdp_url : str or None
        When given, attach to an already-running Chrome at this DevTools
        endpoint instead of launching headless Chromium. This is the only way
        to read pages behind a login: the headless default carries no session,
        so an authenticated URL comes back as the site's login page.
    open_page : callable or None
        Injected async context manager ``open_page(url, *, wait_until,
        timeout_ms)`` yielding a navigated page. Defaults to headless
        Chromium; tests pass a stand-in.

    Returns
    -------
    dict
        ``{"url": final URL after redirects, "title": page title,
        "html": markup, "text": visible text}``.
    """
    if open_page is None:
        if cdp_url is None:
            open_page = _chromium_page
        else:
            from ._extract_chat import attach_cdp_page

            @asynccontextmanager
            async def _attach(url, *, wait_until, timeout_ms):
                async with attach_cdp_page(
                    url,
                    wait_until=wait_until,
                    timeout_ms=timeout_ms,
                    cdp_url=cdp_url,
                ) as page:
                    yield page

            open_page = _attach

    url = normalize_url(url)

    async with open_page(url, wait_until=wait_until, timeout_ms=timeout_ms) as page:
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        return await extract_from_page_async(
            page, dismiss_overlays=dismiss_overlays, selector=selector
        )


async def get_html_async(url: str, **kwargs) -> str:
    """Return the rendered HTML of ``url``."""
    return (await fetch_content_async(url, **kwargs))["html"]


async def get_text_async(url: str, **kwargs) -> str:
    """Return the rendered visible text of ``url``."""
    return (await fetch_content_async(url, **kwargs))["text"]


async def _save_async(url: str, output_path: str, key: str, suffix: str, **kwargs):
    content = (await fetch_content_async(url, **kwargs))[key]

    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() != suffix:
        output = output.with_suffix(suffix)

    output.write_text(content, encoding="utf-8")
    return str(output)


async def save_as_html_async(url: str, output_path: str, **kwargs) -> str:
    """Save the rendered HTML of ``url`` to ``output_path``.

    Returns the absolute path actually written (the extension is normalized
    to ``.html``).
    """
    return await _save_async(url, output_path, "html", ".html", **kwargs)


async def save_as_text_async(url: str, output_path: str, **kwargs) -> str:
    """Save the rendered visible text of ``url`` to ``output_path``.

    Returns the absolute path actually written (the extension is normalized
    to ``.txt``).
    """
    return await _save_async(url, output_path, "text", ".txt", **kwargs)


def fetch_content(url: str, **kwargs) -> dict:
    """Sync wrapper for :func:`fetch_content_async`."""
    return asyncio.run(fetch_content_async(url, **kwargs))


def get_html(url: str, **kwargs) -> str:
    """Sync wrapper for :func:`get_html_async`."""
    return asyncio.run(get_html_async(url, **kwargs))


def get_text(url: str, **kwargs) -> str:
    """Sync wrapper for :func:`get_text_async`."""
    return asyncio.run(get_text_async(url, **kwargs))


def save_as_html(url: str, output_path: str, **kwargs) -> str:
    """Sync wrapper for :func:`save_as_html_async`."""
    return asyncio.run(save_as_html_async(url, output_path, **kwargs))


def save_as_text(url: str, output_path: str, **kwargs) -> str:
    """Sync wrapper for :func:`save_as_text_async`."""
    return asyncio.run(save_as_text_async(url, output_path, **kwargs))


# EOF
