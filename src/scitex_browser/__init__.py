from __future__ import annotations

try:
    from importlib.metadata import version as _v, PackageNotFoundError
    try:
        __version__ = _v("scitex-browser")
    except PackageNotFoundError:
        __version__ = "0.0.0+local"
    del _v, PackageNotFoundError
except ImportError:  # pragma: no cover — only on ancient Pythons
    __version__ = "0.0.0+local"

#!/usr/bin/env python3
# SciTeX Browser Utilities - Universal Playwright helpers organized by category
# ----------------------------------------
#
# playwright is a hard dependency (see pyproject.toml) so these imports are
# unconditional. Submodules are imported explicitly first so that
# ``scitex_browser.debugging`` / ``.pdf`` / ``.interaction`` are always
# registered as attributes on the parent package — required by tests that
# do unittest.mock.patch("scitex_browser.debugging.<module>.<name>").

from . import debugging, interaction, pdf  # register submodules as attributes
from .debugging import (
    SyncBrowserSession,
    TestMonitor,
    browser_logger,
    collect_console_logs,
    collect_console_logs_detailed,
    create_browser_session_fixture,
    create_failure_capture_fixture,
    create_test_monitor_fixture,
    format_logs_devtools_style,
    highlight_element_async,
    inject_visual_effects,
    inject_visual_effects_async,
    monitor_test,
    save_failure_artifacts,
    setup_console_interceptor,
    show_click_effect,
    show_click_effect_async,
    show_cursor_at,
    show_cursor_at_async,
    show_grid_async,
    show_step,
    show_step_async,
    show_test_result,
    show_test_result_async,
    sync_browser_session,
)
from .interaction import (
    PopupHandler,
    click_center_async,
    click_with_fallbacks_async,
    close_popups_async,
    ensure_no_popups_async,
    fill_with_fallbacks_async,
)
from .pdf import (
    click_download_for_chrome_pdf_viewer_async,
    detect_chrome_pdf_viewer_async,
    save_as_pdf,
    save_as_pdf_async,
)


def is_playwright_cli_available() -> bool:
    """Check if playwright-cli (npm) is installed."""
    import shutil

    return shutil.which("playwright-cli") is not None


__all__ = [
    "__version__",
    # Utilities
    "is_playwright_cli_available",
    # Debugging
    "browser_logger",
    "show_grid_async",
    "highlight_element_async",
    # Visual cursor/feedback (sync)
    "inject_visual_effects",
    "show_cursor_at",
    "show_click_effect",
    "show_step",
    "show_test_result",
    # Visual cursor/feedback (async)
    "inject_visual_effects_async",
    "show_cursor_at_async",
    "show_click_effect_async",
    "show_step_async",
    "show_test_result_async",
    # Failure capture utilities (mirrors console-interceptor.ts)
    "setup_console_interceptor",
    "collect_console_logs",
    "collect_console_logs_detailed",
    "format_logs_devtools_style",
    "save_failure_artifacts",
    "create_failure_capture_fixture",
    # Test monitoring (periodic screenshots via scitex.capture)
    "TestMonitor",
    "create_test_monitor_fixture",
    "monitor_test",
    # Sync browser session for zombie prevention
    "SyncBrowserSession",
    "sync_browser_session",
    "create_browser_session_fixture",
    # PDF
    "save_as_pdf",
    "save_as_pdf_async",
    "detect_chrome_pdf_viewer_async",
    "click_download_for_chrome_pdf_viewer_async",
    # Interaction
    "click_center_async",
    "click_with_fallbacks_async",
    "fill_with_fallbacks_async",
    "PopupHandler",
    "close_popups_async",
    "ensure_no_popups_async",
]

# EOF
