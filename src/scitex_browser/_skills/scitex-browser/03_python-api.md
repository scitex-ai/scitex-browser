---
description: |
  [TOPIC] Python Api
  [DETAILS] Python API — see file body for details.
tags: [scitex-browser-python-api]
---

# Python API

All symbols listed here are re-exported from top-level `scitex_browser`.
Sub-packages (`debugging`, `interaction`, `pdf`, `auth`, `automation`,
`stealth`, `remote`, `collaboration`, `core`) are also addressable
directly, e.g. `scitex_browser.debugging.TestMonitor`.

## Top-level utility

* `is_playwright_cli_available()` — returns `True` if `playwright-cli` (npm) is on PATH.

## debugging

* `browser_logger` — preconfigured logger instance
* `SyncBrowserSession`, `sync_browser_session`, `create_browser_session_fixture` — zombie-safe sync session
* `TestMonitor`, `create_test_monitor_fixture`, `monitor_test` — periodic screenshot monitor
* `inject_visual_effects`, `show_cursor_at`, `show_click_effect`, `show_step`, `show_test_result` (sync)
* `inject_visual_effects_async`, `show_cursor_at_async`, `show_click_effect_async`, `show_step_async`, `show_test_result_async`, `show_grid_async`, `highlight_element_async` (async)
* `setup_console_interceptor`, `collect_console_logs`, `collect_console_logs_detailed`, `format_logs_devtools_style` — console capture
* `save_failure_artifacts`, `create_failure_capture_fixture` — on-failure screenshots + logs

## interaction

* `click_center_async`, `click_with_fallbacks_async`, `fill_with_fallbacks_async` — resilient input
* `PopupHandler`, `close_popups_async`, `ensure_no_popups_async` — popup dismissal

## pdf

* `save_as_pdf`, `save_as_pdf_async`
* `detect_chrome_pdf_viewer_async`, `click_download_for_chrome_pdf_viewer_async`

## auth (via `scitex_browser.auth`)

* `GoogleAuthHelper`, `google_login`

## automation

* `CookieAutoAcceptor` (None if playwright missing)

## stealth

* `StealthManager`, `HumanBehavior`

## remote

* `ZenRowsAPIBrowser`, `ZenRowsRemoteScholarBrowserManager`, `CaptchaHandler`

## collaboration (experimental)

* `SharedBrowserSession`, `SessionConfig`, `CredentialManager`, `VisualFeedback`

## core

* `BrowserMixin`, `ChromeProfileManager` (both optional)
