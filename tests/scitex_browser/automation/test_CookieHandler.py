#!/usr/bin/env python3
"""Tests for CookieAutoAcceptor class.

History: prior to 2026-05-24 this file used ``unittest.mock`` to stand in
for the Playwright ``BrowserContext`` and ``Page`` collaborators in
``inject_auto_acceptor_async`` / ``check_cookie_banner_exists_async``,
and contained a long tail of degenerate ``test_full_workflow_*`` tests
that re-asserted the same three constants. Under the no-mocks rule
(PA-306) the mocks have been replaced with hand-rolled fakes exposing
only the attributes the SUT touches; under TQ001/TQ007 the degenerate
duplicates have been dropped. Each remaining test asserts one fact via
``# Arrange / # Act / # Assert`` markers and a ≥3-token name.
"""

from __future__ import annotations

import json
import logging as _stdlogging
import os
from dataclasses import dataclass, field

import pytest

from scitex_browser.automation.CookieHandler import CookieAutoAcceptor


# ---------------------------------------------------------------------------
# Hand-rolled async fakes (no unittest.mock)
# ---------------------------------------------------------------------------


@dataclass
class FakeBrowserContext:
    """Stand-in for ``playwright.async_api.BrowserContext`` exposing only
    ``add_init_script(script)``, which is the single method
    ``inject_auto_acceptor_async`` calls. Each call is appended to
    ``scripts`` so tests can observe what production sent.
    """

    scripts: list[str] = field(default_factory=list)

    async def add_init_script(self, script: str) -> None:
        self.scripts.append(script)


@dataclass
class FakeLocatorFirst:
    """Stand-in for the ``Locator.first`` accessor's ``is_visible()``."""

    visible: bool

    async def is_visible(self) -> bool:
        return self.visible


@dataclass
class FakeLocator:
    """Stand-in for ``Locator`` exposing only ``.first.is_visible()``."""

    visible: bool

    @property
    def first(self) -> FakeLocatorFirst:
        return FakeLocatorFirst(visible=self.visible)


@dataclass
class FakeLocatorPage:
    """Stand-in for ``Page`` exposing only ``.locator(selector)``.

    Records each call's selector under ``selectors_seen`` so tests can
    assert on what production queried.
    """

    visible: bool = True
    selectors_seen: list[str] = field(default_factory=list)

    def locator(self, selector: str) -> FakeLocator:
        self.selectors_seen.append(selector)
        return FakeLocator(visible=self.visible)


class FakeRaisingLocatorPage:
    """Stand-in for a ``Page`` whose ``.locator()`` raises — used to
    verify the SUT's ``except`` branch.
    """

    def locator(self, selector: str):
        raise RuntimeError(f"locator failed for: {selector}")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def acceptor() -> CookieAutoAcceptor:
    """Fresh CookieAutoAcceptor per test."""
    return CookieAutoAcceptor()


@pytest.fixture
def script(acceptor: CookieAutoAcceptor) -> str:
    """The full auto-acceptor JavaScript string."""
    return acceptor.get_auto_acceptor_script()


# ---------------------------------------------------------------------------
# Init / attribute presence
# ---------------------------------------------------------------------------


class TestCookieAutoAcceptorInit:
    """Tests for CookieAutoAcceptor initialization."""

    def test_init_sets_name_to_class_name(self, acceptor):
        # Arrange
        # Act
        name = acceptor.name
        # Assert
        assert name == "CookieAutoAcceptor"

    def test_init_assigns_cookie_texts_as_list(self, acceptor):
        # Arrange
        # Act
        texts = acceptor.cookie_texts
        # Assert
        assert isinstance(texts, list)

    def test_init_populates_cookie_texts_with_entries(self, acceptor):
        # Arrange
        # Act
        count = len(acceptor.cookie_texts)
        # Assert
        assert count > 0

    def test_init_assigns_selectors_as_list(self, acceptor):
        # Arrange
        # Act
        selectors = acceptor.selectors
        # Assert
        assert isinstance(selectors, list)

    def test_init_populates_selectors_with_entries(self, acceptor):
        # Arrange
        # Act
        count = len(acceptor.selectors)
        # Assert
        assert count > 0


# ---------------------------------------------------------------------------
# cookie_texts content
# ---------------------------------------------------------------------------


_EXPECTED_TEXTS = ("Accept All", "Accept", "OK", "Agree", "Continue", "I Accept")


@pytest.mark.parametrize("expected_text", _EXPECTED_TEXTS)
def test_cookie_texts_contains_expected_phrase(acceptor, expected_text):
    # Arrange
    texts = acceptor.cookie_texts
    # Act
    present = expected_text in texts
    # Assert
    assert present is True


# ---------------------------------------------------------------------------
# selectors content
# ---------------------------------------------------------------------------


_EXPECTED_SELECTORS = (
    "[data-testid*='accept']",
    "[id*='accept']",
    "[class*='accept']",
    "button[aria-label*='Accept']",
    ".cookie-banner button:first-of-type",
)


@pytest.mark.parametrize("expected_selector", _EXPECTED_SELECTORS)
def test_selectors_list_contains_expected_selector(acceptor, expected_selector):
    # Arrange
    selectors = acceptor.selectors
    # Act
    present = expected_selector in selectors
    # Assert
    assert present is True


# ---------------------------------------------------------------------------
# get_auto_acceptor_script
# ---------------------------------------------------------------------------


class TestGetAutoAcceptorScript:
    """Tests for get_auto_acceptor_script()."""

    def test_script_returns_string_type(self, script):
        # Arrange
        # Act
        kind = type(script)
        # Assert
        assert kind is str

    def test_script_returns_non_empty_string(self, script):
        # Arrange
        # Act
        size = len(script)
        # Assert
        assert size > 0

    def test_script_embeds_first_cookie_text_entries(self, acceptor, script):
        # Arrange
        first_three = acceptor.cookie_texts[:3]
        # Act
        all_present = all(t in script for t in first_three)
        # Assert
        assert all_present is True

    def test_script_embeds_first_selector_entries(self, acceptor, script):
        # Arrange
        first_two = acceptor.selectors[:2]
        # Act
        all_present = all(s in script for s in first_two)
        # Assert
        assert all_present is True

    def test_script_defines_accept_cookies_function(self, script):
        # Arrange
        # Act
        present = "function acceptCookies()" in script
        # Assert
        assert present is True

    def test_script_uses_setinterval_for_periodic_checking(self, script):
        # Arrange
        # Act
        present = "setInterval" in script
        # Assert
        assert present is True

    def test_script_uses_settimeout_for_cleanup(self, script):
        # Arrange
        # Act
        present = "setTimeout" in script
        # Assert
        assert present is True

    def test_script_includes_thirty_second_cleanup_timeout(self, script):
        # Arrange
        # Act
        present = "30000" in script
        # Assert
        assert present is True

    def test_script_skips_buttons_with_scitex_no_auto_click_attribute(self, script):
        # Arrange
        # Act
        present = "data-scitex-no-auto-click" in script
        # Assert
        assert present is True

    def test_script_includes_scitex_id_guard(self, script):
        # Arrange
        # Act
        present = "scitex" in script.lower()
        # Assert
        assert present is True

    def test_script_uses_query_selector_all_for_lookup(self, script):
        # Arrange
        # Act
        present = "querySelectorAll" in script
        # Assert
        assert present is True

    def test_script_checks_element_visibility_via_offsetparent(self, script):
        # Arrange
        # Act
        present = "offsetParent" in script
        # Assert
        assert present is True

    def test_script_opens_with_iife_arrow_form(self, script):
        # Arrange
        # Act
        present = "(() => {" in script
        # Assert
        assert present is True

    def test_script_closes_with_iife_invocation(self, script):
        # Arrange
        # Act
        present = "})();" in script
        # Assert
        assert present is True

    def test_script_embeds_cookie_texts_as_json_array(self, acceptor, script):
        # Arrange
        expected_json = json.dumps(acceptor.cookie_texts)
        # Act
        present = expected_json in script
        # Assert
        assert present is True


# ---------------------------------------------------------------------------
# inject_auto_acceptor_async (uses FakeBrowserContext)
# ---------------------------------------------------------------------------


class TestInjectAutoAcceptorAsync:
    """Tests for inject_auto_acceptor_async with a hand-rolled context fake."""

    @pytest.mark.asyncio
    async def test_inject_invokes_add_init_script_once(self, acceptor):
        # Arrange
        ctx = FakeBrowserContext()
        # Act
        await acceptor.inject_auto_acceptor_async(ctx)
        # Assert
        assert len(ctx.scripts) == 1

    @pytest.mark.asyncio
    async def test_inject_sends_script_containing_accept_cookies(self, acceptor):
        # Arrange
        ctx = FakeBrowserContext()
        # Act
        await acceptor.inject_auto_acceptor_async(ctx)
        # Assert
        assert "acceptCookies" in ctx.scripts[0]

    @pytest.mark.asyncio
    async def test_inject_emits_deprecation_warning_through_logger(
        self, acceptor, caplog
    ):
        # Arrange
        ctx = FakeBrowserContext()
        caplog.set_level(
            _stdlogging.WARNING, logger="scitex_browser.automation.CookieHandler"
        )
        # Act
        await acceptor.inject_auto_acceptor_async(ctx)
        # Assert
        assert any(rec.levelno >= _stdlogging.WARNING for rec in caplog.records)


# ---------------------------------------------------------------------------
# check_cookie_banner_exists_async (uses FakeLocatorPage)
# ---------------------------------------------------------------------------


class TestCheckCookieBannerExistsAsync:
    """Tests for check_cookie_banner_exists_async with a hand-rolled page fake."""

    @pytest.mark.asyncio
    async def test_returns_true_when_locator_first_is_visible(self, acceptor):
        # Arrange
        page = FakeLocatorPage(visible=True)
        # Act
        result = await acceptor.check_cookie_banner_exists_async(page)
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_locator_first_is_hidden(self, acceptor):
        # Arrange
        page = FakeLocatorPage(visible=False)
        # Act
        result = await acceptor.check_cookie_banner_exists_async(page)
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_page_locator_raises(self, acceptor):
        # Arrange
        page = FakeRaisingLocatorPage()
        # Act
        result = await acceptor.check_cookie_banner_exists_async(page)
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_queries_page_with_cookie_banner_class_in_selector(
        self, acceptor
    ):
        # Arrange
        page = FakeLocatorPage(visible=True)
        # Act
        await acceptor.check_cookie_banner_exists_async(page)
        # Assert
        assert ".cookie-banner" in page.selectors_seen[0]

    @pytest.mark.asyncio
    async def test_queries_page_with_cookie_class_wildcard_in_selector(
        self, acceptor
    ):
        # Arrange
        page = FakeLocatorPage(visible=True)
        # Act
        await acceptor.check_cookie_banner_exists_async(page)
        # Assert
        assert "[class*='cookie']" in page.selectors_seen[0]


# ---------------------------------------------------------------------------
# Instance independence
# ---------------------------------------------------------------------------


class TestCookieAutoAcceptorInstanceIndependence:
    """Tests verifying instance state is per-object, not shared."""

    def test_mutating_one_instance_cookie_texts_does_not_affect_another(self):
        # Arrange
        first = CookieAutoAcceptor()
        second = CookieAutoAcceptor()
        # Act
        first.cookie_texts.append("Custom Text")
        # Assert
        assert "Custom Text" not in second.cookie_texts


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__), "-v"])
