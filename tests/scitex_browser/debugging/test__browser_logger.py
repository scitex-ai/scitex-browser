#!/usr/bin/env python3
"""Tests for the browser_logger module.

History: prior to 2026-05-24 this file used ``unittest.mock`` /
``AsyncMock`` to stand in for the Playwright ``Page`` collaborator
throughout ``log_page_async`` and ``BrowserLogger``. Many of those tests
asserted on ``mock.<method>.called`` / ``mock.assert_*`` rather than on
production output — green-bar theater under PA-306. One test even
patched ``get_paths`` despite production using ``screenshots_dir``,
which made it provably untrue. Under the no-mocks rule the mocks have
been replaced with hand-rolled async ``FakePage`` flavors and the
stale/duplicate tests have been dropped or consolidated.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from scitex_browser.debugging._browser_logger import (
    _POPUP_COLORS,
    BrowserLogger,
    browser_logger,
    log_page_async,
)


# ---------------------------------------------------------------------------
# Hand-rolled async Page fakes (no unittest.mock)
# ---------------------------------------------------------------------------


@dataclass
class FakeFrame:
    """Stand-in for a Playwright ``Frame`` — equality is identity-based."""


class FakePage:
    """Minimal stand-in for Playwright ``Page`` exposing only the
    attributes / coroutine methods that ``log_page_async`` touches:

    - ``is_closed()`` (sync)
    - ``evaluate(js)`` (async, records each call)
    - ``on(event, handler)`` (sync, records each call)
    - ``main_frame`` (attribute, used by re-injection handler)
    - ``wait_for_timeout(ms)`` (async)
    - ``screenshot(path=..., full_page=...)`` (async)
    - ``wait_for_load_state(state, timeout=...)`` (async)
    """

    def __init__(
        self,
        *,
        closed: bool = False,
        evaluate_raises: bool = False,
        screenshot_raises: bool = False,
    ) -> None:
        self._closed = closed
        self._evaluate_raises = evaluate_raises
        self._screenshot_raises = screenshot_raises
        self.evaluate_calls: list[str] = []
        self.on_calls: list[tuple[str, object]] = []
        self.screenshot_paths: list[str] = []
        self.timeouts: list[int] = []
        self.main_frame = FakeFrame()

    def is_closed(self) -> bool:
        return self._closed

    async def evaluate(self, js: str) -> None:
        self.evaluate_calls.append(js)
        if self._evaluate_raises:
            raise RuntimeError("evaluate failed")

    def on(self, event: str, handler) -> None:
        self.on_calls.append((event, handler))

    async def wait_for_timeout(self, ms: int) -> None:
        self.timeouts.append(ms)

    async def wait_for_load_state(self, state: str, timeout: int = 5000) -> None:
        pass

    async def screenshot(self, *, path: str, full_page: bool = False) -> None:
        self.screenshot_paths.append(path)
        if self._screenshot_raises:
            raise RuntimeError("screenshot failed")


# ---------------------------------------------------------------------------
# _POPUP_COLORS constants
# ---------------------------------------------------------------------------


class TestPopupColorsConstant:
    """Tests for the _POPUP_COLORS dict shape."""

    def test_popup_colors_is_dict_type(self):
        # Arrange
        # Act
        kind = type(_POPUP_COLORS)
        # Assert
        assert kind is dict


@pytest.mark.parametrize(
    "level,expected_hex",
    [
        ("debug", "#6C757D"),
        ("info", "#17A2B8"),
        ("success", "#28A745"),
        ("warning", "#FFC107"),
        ("error", "#DC3545"),
        ("fail", "#DC3545"),
    ],
)
def test_popup_colors_level_maps_to_expected_hex(level, expected_hex):
    # Arrange
    table = _POPUP_COLORS
    # Act
    actual = table[level]
    # Assert
    assert actual == expected_hex


# ---------------------------------------------------------------------------
# log_page_async — verbose=False early exit
# ---------------------------------------------------------------------------


class TestLogPageAsyncVerboseFalse:
    """When verbose=False the function returns True without touching the page."""

    @pytest.mark.asyncio
    async def test_returns_true_when_verbose_false_and_page_is_none(self):
        # Arrange
        # Act
        result = await log_page_async(page=None, message="m", verbose=False)
        # Assert
        assert result is True


# ---------------------------------------------------------------------------
# log_page_async — page=None / closed page in verbose mode
# ---------------------------------------------------------------------------


class TestLogPageAsyncPageGuards:
    """Tests for verbose=True with absent or closed pages."""

    @pytest.mark.asyncio
    async def test_returns_false_when_verbose_true_and_page_is_none(self):
        # Arrange
        # Act
        result = await log_page_async(page=None, message="m", verbose=True)
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_page_is_closed(self):
        # Arrange
        page = FakePage(closed=True)
        # Act
        result = await log_page_async(page=page, message="m", verbose=True)
        # Assert
        assert result is False


# ---------------------------------------------------------------------------
# log_page_async — happy path with a hand-rolled FakePage
# ---------------------------------------------------------------------------


class TestLogPageAsyncHappyPath:
    """Tests for the verbose=True happy path against FakePage."""

    @pytest.mark.asyncio
    async def test_returns_true_for_default_info_level(self):
        # Arrange
        page = FakePage()
        # Act
        result = await log_page_async(
            page=page,
            message="hello",
            verbose=True,
            take_screenshot=False,
        )
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_true_when_custom_duration_supplied(self):
        # Arrange
        page = FakePage()
        # Act
        result = await log_page_async(
            page=page,
            message="hello",
            duration_ms=30_000,
            verbose=True,
            take_screenshot=False,
        )
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_evaluates_popup_js_at_least_once_in_verbose_mode(self):
        # Arrange
        page = FakePage()
        # Act
        await log_page_async(
            page=page,
            message="hello",
            verbose=True,
            take_screenshot=False,
        )
        # Assert
        assert len(page.evaluate_calls) >= 1

    @pytest.mark.asyncio
    async def test_returns_false_when_page_evaluate_raises(self):
        # Arrange
        page = FakePage(evaluate_raises=True)
        # Act
        result = await log_page_async(
            page=page,
            message="hello",
            verbose=True,
            take_screenshot=False,
        )
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_registers_framenavigated_handler_on_first_call(self):
        # Arrange
        page = FakePage()
        # Act
        await log_page_async(
            page=page,
            message="hello",
            verbose=True,
            take_screenshot=False,
        )
        # Assert
        assert any(event == "framenavigated" for event, _ in page.on_calls)


# ---------------------------------------------------------------------------
# log_page_async — log level filtering / explicit error level
# ---------------------------------------------------------------------------


class TestLogPageAsyncLogLevelHandling:
    """log_page_async accepts an explicit ``level`` argument."""

    @pytest.mark.asyncio
    async def test_debug_level_call_returns_true(self):
        # Arrange
        page = FakePage()
        # Act
        result = await log_page_async(
            page=page,
            message="debug",
            level="debug",
            verbose=True,
            take_screenshot=False,
        )
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_error_level_call_returns_true(self):
        # Arrange
        page = FakePage()
        # Act
        result = await log_page_async(
            page=page,
            message="error",
            level="error",
            verbose=True,
            take_screenshot=False,
        )
        # Assert
        assert result is True


# ---------------------------------------------------------------------------
# log_page_async — screenshot routing into tmp_path
# ---------------------------------------------------------------------------


class TestLogPageAsyncScreenshot:
    """Tests for screenshot capture against a real on-disk tmp directory."""

    @pytest.mark.asyncio
    async def test_does_not_call_page_screenshot_when_take_screenshot_false(
        self, tmp_path
    ):
        # Arrange
        page = FakePage()
        # Act
        await log_page_async(
            page=page,
            message="m",
            take_screenshot=False,
            verbose=True,
        )
        # Assert
        assert page.screenshot_paths == []

    @pytest.mark.asyncio
    async def test_calls_page_screenshot_when_take_screenshot_true(
        self, tmp_path
    ):
        # Arrange
        page = FakePage()
        screenshot_dir = tmp_path / "shots"
        # Act
        await log_page_async(
            page=page,
            message="hello",
            take_screenshot=True,
            screenshot_dir=screenshot_dir,
            verbose=True,
        )
        # Assert
        assert len(page.screenshot_paths) == 1

    @pytest.mark.asyncio
    async def test_writes_screenshot_under_supplied_screenshot_dir(
        self, tmp_path
    ):
        # Arrange
        page = FakePage()
        screenshot_dir = tmp_path / "shots"
        # Act
        await log_page_async(
            page=page,
            message="hello",
            take_screenshot=True,
            screenshot_dir=screenshot_dir,
            verbose=True,
        )
        # Assert
        assert str(screenshot_dir) in page.screenshot_paths[0]

    @pytest.mark.asyncio
    async def test_creates_screenshot_dir_on_disk(self, tmp_path):
        # Arrange
        page = FakePage()
        screenshot_dir = tmp_path / "fresh-shots"
        # Act
        await log_page_async(
            page=page,
            message="hello",
            take_screenshot=True,
            screenshot_dir=screenshot_dir,
            verbose=True,
        )
        # Assert
        assert screenshot_dir.is_dir()


# ---------------------------------------------------------------------------
# BrowserLogger.__init__
# ---------------------------------------------------------------------------


class TestBrowserLoggerInit:
    """Tests for BrowserLogger initialization."""

    def test_default_page_attribute_is_none(self):
        # Arrange
        # Act
        logger = BrowserLogger()
        # Assert
        assert logger.page is None

    def test_default_duration_ms_is_sixty_thousand(self):
        # Arrange
        # Act
        logger = BrowserLogger()
        # Assert
        assert logger.duration_ms == 60_000

    def test_default_take_screenshot_is_true(self):
        # Arrange
        # Act
        logger = BrowserLogger()
        # Assert
        assert logger.take_screenshot is True

    def test_default_screenshot_dir_is_none(self):
        # Arrange
        # Act
        logger = BrowserLogger()
        # Assert
        assert logger.screenshot_dir is None

    def test_default_verbose_is_true(self):
        # Arrange
        # Act
        logger = BrowserLogger()
        # Assert
        assert logger.verbose is True

    def test_custom_page_is_stored_as_attribute(self):
        # Arrange
        page = FakePage()
        # Act
        logger = BrowserLogger(page=page)
        # Assert
        assert logger.page is page

    def test_custom_duration_ms_is_stored_as_attribute(self):
        # Arrange
        # Act
        logger = BrowserLogger(duration_ms=30_000)
        # Assert
        assert logger.duration_ms == 30_000

    def test_custom_take_screenshot_false_is_stored_as_attribute(self):
        # Arrange
        # Act
        logger = BrowserLogger(take_screenshot=False)
        # Assert
        assert logger.take_screenshot is False

    def test_custom_screenshot_dir_path_is_stored_as_attribute(self):
        # Arrange
        # Act
        logger = BrowserLogger(screenshot_dir="/custom/path")
        # Assert
        assert logger.screenshot_dir == "/custom/path"

    def test_custom_verbose_false_is_stored_as_attribute(self):
        # Arrange
        # Act
        logger = BrowserLogger(verbose=False)
        # Assert
        assert logger.verbose is False


# ---------------------------------------------------------------------------
# BrowserLogger.<level>(...) — each level method delegates to log_page_async
# ---------------------------------------------------------------------------


@pytest.fixture
def quiet_logger() -> BrowserLogger:
    """BrowserLogger with verbose=False so each level call returns True
    immediately (short-circuits inside log_page_async)."""
    return BrowserLogger(verbose=False)


@pytest.fixture
def open_fake_page() -> FakePage:
    """A real open FakePage. Used purely for identity / collaborator
    contract — the verbose=False short-circuit means the page is not
    touched."""
    return FakePage()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method_name",
    ["debug", "info", "success", "warning", "warn", "error", "fail"],
)
async def test_browser_logger_level_method_returns_true_when_verbose_false(
    quiet_logger, open_fake_page, method_name
):
    # Arrange
    method = getattr(quiet_logger, method_name)
    # Act
    result = await method(open_fake_page, "msg")
    # Assert
    assert result is True


class TestBrowserLoggerLevelMethodKwargs:
    """Tests for keyword-argument acceptance on level methods."""

    @pytest.mark.asyncio
    async def test_info_accepts_explicit_duration_ms_kwarg(
        self, quiet_logger, open_fake_page
    ):
        # Arrange
        # Act
        result = await quiet_logger.info(
            open_fake_page, "msg", duration_ms=5_000
        )
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_info_accepts_explicit_take_screenshot_kwarg(
        self, quiet_logger, open_fake_page
    ):
        # Arrange
        # Act
        result = await quiet_logger.info(
            open_fake_page, "msg", take_screenshot=False
        )
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_info_accepts_explicit_screenshot_dir_kwarg(
        self, quiet_logger, open_fake_page, tmp_path
    ):
        # Arrange
        # Act
        result = await quiet_logger.info(
            open_fake_page,
            "msg",
            screenshot_dir=str(tmp_path / "custom"),
        )
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_info_accepts_explicit_func_name_kwarg(
        self, quiet_logger, open_fake_page
    ):
        # Arrange
        # Act
        result = await quiet_logger.info(
            open_fake_page, "msg", func_name="CustomFunc"
        )
        # Assert
        assert result is True


# ---------------------------------------------------------------------------
# BrowserLogger._log delegation contract (uses verbose-True end-to-end)
# ---------------------------------------------------------------------------


class TestBrowserLoggerLogDelegation:
    """Verify ``_log`` delegates kwargs through to log_page_async by
    observing real production effects (popup evaluate calls, screenshot
    paths) against the FakePage — no patching."""

    @pytest.mark.asyncio
    async def test_log_invokes_page_evaluate_when_verbose_true(self):
        # Arrange
        logger = BrowserLogger(verbose=True)
        page = FakePage()
        # Act
        await logger._log(page, "info", "hello", take_screenshot=False)
        # Assert
        assert len(page.evaluate_calls) >= 1

    @pytest.mark.asyncio
    async def test_log_returns_false_when_page_is_closed(self):
        # Arrange
        logger = BrowserLogger(verbose=True)
        page = FakePage(closed=True)
        # Act
        result = await logger._log(page, "info", "hello")
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_log_routes_screenshot_to_supplied_directory(self, tmp_path):
        # Arrange
        logger = BrowserLogger(verbose=True)
        page = FakePage()
        target = tmp_path / "routed"
        # Act
        await logger._log(
            page,
            "info",
            "hello",
            take_screenshot=True,
            screenshot_dir=target,
        )
        # Assert
        assert str(target) in page.screenshot_paths[0]

    @pytest.mark.asyncio
    async def test_log_falls_back_to_instance_screenshot_dir_when_arg_missing(
        self, tmp_path
    ):
        # Arrange
        default = tmp_path / "instance-default"
        logger = BrowserLogger(verbose=True, screenshot_dir=default)
        page = FakePage()
        # Act
        await logger._log(page, "info", "hello", take_screenshot=True)
        # Assert
        assert str(default) in page.screenshot_paths[0]


# ---------------------------------------------------------------------------
# Module-level browser_logger instance
# ---------------------------------------------------------------------------


class TestGlobalBrowserLoggerInstance:
    """Tests for the module-level ``browser_logger`` singleton."""

    def test_module_global_logger_is_browserlogger_instance(self):
        # Arrange
        # Act
        kind = type(browser_logger)
        # Assert
        assert kind is BrowserLogger

    def test_module_global_logger_default_page_is_none(self):
        # Arrange
        # Act
        page = browser_logger.page
        # Assert
        assert page is None

    def test_module_global_logger_default_duration_ms_is_sixty_thousand(self):
        # Arrange
        # Act
        duration = browser_logger.duration_ms
        # Assert
        assert duration == 60_000

    def test_module_global_logger_default_take_screenshot_is_true(self):
        # Arrange
        # Act
        flag = browser_logger.take_screenshot
        # Assert
        assert flag is True

    def test_module_global_logger_default_verbose_is_true(self):
        # Arrange
        # Act
        flag = browser_logger.verbose
        # Assert
        assert flag is True


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__), "-v"])
