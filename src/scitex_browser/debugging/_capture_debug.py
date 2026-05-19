"""Async debug-artifact capture for live browser pages.

Browser automation is fundamentally unreliable: selectors drift,
SSO flows change, MFA pages mutate. Always-on screenshot + HTML
capture turns "the script hung" into a forensic trail.

This module exposes one async helper:

    await capture_debug_artifacts_async(page, label, base_dir=None)

It writes:
    <base_dir>/<label>_<ts>.png    full-page screenshot
    <base_dir>/<label>_<ts>.html   page.content() snapshot

`base_dir` defaults to ``$SCITEX_DIR/browser/runtime/cache/debug/``
(``~/.scitex/browser/runtime/cache/debug/`` when ``SCITEX_DIR`` is
unset). Failures are swallowed and logged at debug level — a broken
capture must never break the caller's flow. Returns the
(png_path, html_path) tuple, or (None, None) on total failure.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Tuple

from scitex_browser._state import cache_dir

if TYPE_CHECKING:  # pragma: no cover
    from playwright.async_api import Page

logger = logging.getLogger(__name__)


def _default_base_dir() -> Path:
    return cache_dir() / "debug"


async def capture_debug_artifacts_async(
    page: "Page",
    label: str,
    base_dir: Path | str | None = None,
    *,
    full_page: bool = True,
    include_html: bool = True,
) -> Tuple[Path | None, Path | None]:
    """Save a screenshot and (optionally) the page HTML.

    Parameters
    ----------
    page : playwright.async_api.Page
        Live page object.
    label : str
        Short tag used as the filename prefix (e.g. "mfa_picker_before").
        Sanitized: non-alphanum chars become "_".
    base_dir : path-like or None
        Where to write. Defaults to ``$SCITEX_DIR/browser/runtime/cache/debug/``
        (``~/.scitex/browser/runtime/cache/debug/`` by default).
    full_page : bool
        Capture the full scrollable page (default True). Pass False for
        viewport-only.
    include_html : bool
        Save ``page.content()`` alongside the screenshot (default True).

    Returns
    -------
    (png_path, html_path)
        Paths actually written, or None on failure.
    """
    safe_label = "".join(c if c.isalnum() or c in "._-" else "_" for c in label)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out_dir = Path(base_dir) if base_dir else _default_base_dir()

    png_path: Path | None = None
    html_path: Path | None = None
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.debug(f"capture_debug_artifacts_async: mkdir failed: {e}")
        return None, None

    png_target = out_dir / f"{safe_label}_{ts}.png"
    try:
        await page.screenshot(path=str(png_target), full_page=full_page)
        png_path = png_target
        logger.info(f"Debug screenshot: {png_target}")
    except Exception as e:
        logger.debug(f"capture_debug_artifacts_async: screenshot failed: {e}")

    if include_html:
        html_target = out_dir / f"{safe_label}_{ts}.html"
        try:
            content = await page.content()
            html_target.write_text(content, encoding="utf-8")
            html_path = html_target
            logger.info(f"Debug HTML: {html_target}")
        except Exception as e:
            logger.debug(f"capture_debug_artifacts_async: html save failed: {e}")

    return png_path, html_path
