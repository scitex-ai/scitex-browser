#!/usr/bin/env python3
"""Shared page preparation helpers used before capturing a rendered page.

Both PDF capture (:mod:`scitex_browser.pdf`) and content capture
(:mod:`scitex_browser.content`) need to get a freshly-navigated page into a
capturable state. Keeping the logic here means the two capture paths cannot
drift apart.
"""

# Common cookie consent button selectors, tried in order.
_CONSENT_SELECTORS = [
    # Generic patterns
    "button:has-text('Accept all')",
    "button:has-text('Accept All')",
    "button:has-text('Accept all cookies')",
    "button:has-text('Accept All Cookies')",
    "button:has-text('Reject optional cookies')",
    "button:has-text('Reject all')",
    "button:has-text('I agree')",
    "button:has-text('Got it')",
    "button:has-text('OK')",
    "button:has-text('Close')",
    # ID/class patterns
    "[id*='cookie'] button",
    "[class*='cookie'] button",
    "[id*='consent'] button",
    "[class*='consent'] button",
    "[id*='gdpr'] button",
    "[class*='gdpr'] button",
]

# Removes leftover fixed/sticky overlays that survive the consent click.
_REMOVE_OVERLAYS_JS = """
    () => {
        const remove = (el) => {
            const style = window.getComputedStyle(el);
            if (style.position === 'fixed' || style.position === 'sticky') {
                const rect = el.getBoundingClientRect();
                // Only remove large overlays (>30% of viewport width or height)
                if (rect.width > window.innerWidth * 0.3
                    || rect.height > window.innerHeight * 0.3) {
                    el.remove();
                }
            }
        };
        document.querySelectorAll('div, section, aside, footer, header')
            .forEach(remove);
    }
"""


async def dismiss_overlays_async(page) -> None:
    """Dismiss cookie consent banners, popups, and sticky overlays.

    Note that the fallback step removes any large fixed/sticky element, which
    is right for a visual capture but can delete real content on sites that
    lay out results in a sticky container. Content capture therefore leaves
    this off by default; see :func:`scitex_browser.content.fetch_content_async`.

    Parameters
    ----------
    page
        Playwright page object, already navigated.
    """
    for selector in _CONSENT_SELECTORS:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=500):
                await btn.click(timeout=1_000)
                await page.wait_for_timeout(500)
                break
        except Exception:
            continue

    await page.evaluate(_REMOVE_OVERLAYS_JS)
    await page.wait_for_timeout(300)


def normalize_url(url: str) -> str:
    """Add an ``https://`` scheme when the caller omitted one."""
    if not url.startswith(("http://", "https://", "file://")):
        return f"https://{url}"
    return url


# EOF
