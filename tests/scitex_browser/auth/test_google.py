#!/usr/bin/env python3
"""Tests for GoogleAuthHelper class.

History: prior to 2026-05-24 this file used ``unittest.mock`` to stand in
for the Playwright ``Page`` object across the OAuth-popup methods. Those
tests were pure mock theater — they asserted on ``mock.assert_called_*``
rather than on production state — and so were deleted under the SciTeX
no-mocks rule (PA-306). The remaining tests exercise the parts of
``GoogleAuthHelper`` that do NOT need a real browser: instance
construction, env-var fallbacks, debug logging, and the URL-only
``is_logged_in`` heuristic. The popup-flow methods should be covered by
real-browser integration tests under ``tests/integration/``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import pytest

from scitex_browser.auth.google import GoogleAuthHelper


# ---------------------------------------------------------------------------
# Hand-rolled fakes (no unittest.mock)
# ---------------------------------------------------------------------------


@dataclass
class FakeUrlPage:
    """Minimal stand-in for ``playwright.async_api.Page`` exposing just the
    ``url`` attribute that ``GoogleAuthHelper.is_logged_in`` reads.

    The real ``Page`` has ~40 methods; this fake has 1. Renames on the
    production side (e.g. ``page.url`` → ``page.current_url``) will turn
    these tests red — which is exactly the contract we want.
    """

    url: str


# ---------------------------------------------------------------------------
# Env-var fixtures (yield-based, no monkeypatch)
# ---------------------------------------------------------------------------


_GOOGLE_AUTH_ENV_KEYS = ("GOOGLE_EMAIL", "GOOGLE_PASSWORD", "GOOGLE_AUTH_DEBUG")


@pytest.fixture
def google_auth_env_restore():
    """Snapshot and restore the Google-auth env vars across the test.

    Replaces the ``monkeypatch.setenv(...)`` / ``patch.dict(os.environ, ...)``
    pattern.
    """
    saved = {k: os.environ.get(k) for k in _GOOGLE_AUTH_ENV_KEYS}
    for k in _GOOGLE_AUTH_ENV_KEYS:
        os.environ.pop(k, None)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# ---------------------------------------------------------------------------
# Init tests
# ---------------------------------------------------------------------------


class TestGoogleAuthHelperInit:
    """Tests for GoogleAuthHelper initialization."""

    def test_init_creates_instance_when_no_args(self, google_auth_env_restore):
        # Arrange
        # (env cleared by fixture)
        # Act
        auth = GoogleAuthHelper()
        # Assert
        assert auth is not None

    def test_init_stores_email_supplied_as_param(self, google_auth_env_restore):
        # Arrange
        param_email = "test@gmail.com"
        # Act
        auth = GoogleAuthHelper(email=param_email)
        # Assert
        assert auth.email == param_email

    def test_init_stores_password_supplied_as_param(self, google_auth_env_restore):
        # Arrange
        param_password = "secret123"
        # Act
        auth = GoogleAuthHelper(password=param_password)
        # Assert
        assert auth.password == param_password

    def test_init_stores_debug_true_when_supplied(self, google_auth_env_restore):
        # Arrange
        # Act
        auth = GoogleAuthHelper(debug=True)
        # Assert
        assert auth.debug is True

    def test_init_reads_email_from_google_email_env_var(
        self, google_auth_env_restore
    ):
        # Arrange
        os.environ["GOOGLE_EMAIL"] = "env@gmail.com"
        # Act
        auth = GoogleAuthHelper()
        # Assert
        assert auth.email == "env@gmail.com"

    def test_init_reads_password_from_google_password_env_var(
        self, google_auth_env_restore
    ):
        # Arrange
        os.environ["GOOGLE_PASSWORD"] = "envpass"
        # Act
        auth = GoogleAuthHelper()
        # Assert
        assert auth.password == "envpass"

    def test_init_reads_debug_from_google_auth_debug_env_var(
        self, google_auth_env_restore
    ):
        # Arrange
        os.environ["GOOGLE_AUTH_DEBUG"] = "1"
        # Act
        auth = GoogleAuthHelper()
        # Assert
        assert auth.debug is True

    def test_init_prefers_param_email_over_env(self, google_auth_env_restore):
        # Arrange
        os.environ["GOOGLE_EMAIL"] = "env@gmail.com"
        # Act
        auth = GoogleAuthHelper(email="param@gmail.com")
        # Assert
        assert auth.email == "param@gmail.com"

    def test_init_prefers_param_password_over_env(self, google_auth_env_restore):
        # Arrange
        os.environ["GOOGLE_PASSWORD"] = "envpass"
        # Act
        auth = GoogleAuthHelper(password="parampass")
        # Assert
        assert auth.password == "parampass"

    def test_init_defaults_email_to_empty_string_when_unset(
        self, google_auth_env_restore
    ):
        # Arrange
        # (env cleared by fixture)
        # Act
        auth = GoogleAuthHelper()
        # Assert
        assert auth.email == ""

    def test_init_defaults_password_to_empty_string_when_unset(
        self, google_auth_env_restore
    ):
        # Arrange
        # (env cleared by fixture)
        # Act
        auth = GoogleAuthHelper()
        # Assert
        assert auth.password == ""

    def test_init_defaults_debug_to_false_when_unset(self, google_auth_env_restore):
        # Arrange
        # (env cleared by fixture)
        # Act
        auth = GoogleAuthHelper()
        # Assert
        assert auth.debug is False


# ---------------------------------------------------------------------------
# _log tests
# ---------------------------------------------------------------------------


class TestGoogleAuthHelperLog:
    """Tests for the _log method."""

    def test_log_writes_message_text_to_stderr_when_debug_enabled(
        self, capsys, google_auth_env_restore
    ):
        # Arrange
        auth = GoogleAuthHelper(debug=True)
        # Act
        auth._log("Test message")
        # Assert
        assert "Test message" in capsys.readouterr().err

    def test_log_writes_googleauth_tag_to_stderr_when_debug_enabled(
        self, capsys, google_auth_env_restore
    ):
        # Arrange
        auth = GoogleAuthHelper(debug=True)
        # Act
        auth._log("Test message")
        # Assert
        assert "[GoogleAuth]" in capsys.readouterr().err

    def test_log_writes_nothing_to_stderr_when_debug_disabled(
        self, capsys, google_auth_env_restore
    ):
        # Arrange
        auth = GoogleAuthHelper(debug=False)
        # Act
        auth._log("Test message")
        # Assert
        assert capsys.readouterr().err == ""


# ---------------------------------------------------------------------------
# is_logged_in tests (URL-only — exercised with a real hand-rolled page fake)
# ---------------------------------------------------------------------------


class TestGoogleAuthHelperIsLoggedIn:
    """Tests for the is_logged_in heuristic."""

    @pytest.mark.asyncio
    async def test_is_logged_in_returns_false_for_login_in_url(
        self, google_auth_env_restore
    ):
        # Arrange
        auth = GoogleAuthHelper()
        page = FakeUrlPage(url="https://example.com/login")
        # Act
        result = await auth.is_logged_in(page)
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_is_logged_in_returns_false_for_signin_in_url(
        self, google_auth_env_restore
    ):
        # Arrange
        auth = GoogleAuthHelper()
        page = FakeUrlPage(url="https://example.com/signin")
        # Act
        result = await auth.is_logged_in(page)
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_is_logged_in_returns_false_for_oauth_in_url(
        self, google_auth_env_restore
    ):
        # Arrange
        auth = GoogleAuthHelper()
        page = FakeUrlPage(url="https://example.com/oauth/authorize")
        # Act
        result = await auth.is_logged_in(page)
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_is_logged_in_returns_false_for_google_accounts_url(
        self, google_auth_env_restore
    ):
        # Arrange
        auth = GoogleAuthHelper()
        page = FakeUrlPage(url="https://accounts.google.com/signin")
        # Act
        result = await auth.is_logged_in(page)
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_is_logged_in_returns_true_for_dashboard_url(
        self, google_auth_env_restore
    ):
        # Arrange
        auth = GoogleAuthHelper()
        page = FakeUrlPage(url="https://example.com/dashboard")
        # Act
        result = await auth.is_logged_in(page)
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_is_logged_in_honours_custom_indicators_list(
        self, google_auth_env_restore
    ):
        # Arrange
        auth = GoogleAuthHelper()
        page = FakeUrlPage(url="https://example.com/auth")
        # Act
        result = await auth.is_logged_in(page, login_indicators=["auth"])
        # Assert
        assert result is False


# ---------------------------------------------------------------------------
# Multi-instance isolation
# ---------------------------------------------------------------------------


class TestGoogleAuthHelperMultipleInstancesIndependent:
    """Tests that multiple GoogleAuthHelper instances do not share state."""

    @pytest.fixture
    def two_instances(self, google_auth_env_restore):
        return (
            GoogleAuthHelper(email="user1@gmail.com"),
            GoogleAuthHelper(email="user2@gmail.com"),
        )

    def test_two_instances_have_distinct_email_attribute_values(self, two_instances):
        # Arrange
        auth1, auth2 = two_instances
        # Act
        same = auth1.email == auth2.email
        # Assert
        assert same is False

    def test_first_instance_keeps_supplied_email_unchanged(self, two_instances):
        # Arrange
        auth1, _ = two_instances
        # Act
        first_email = auth1.email
        # Assert
        assert first_email == "user1@gmail.com"

    def test_second_instance_keeps_supplied_email_unchanged(self, two_instances):
        # Arrange
        _, auth2 = two_instances
        # Act
        second_email = auth2.email
        # Assert
        assert second_email == "user2@gmail.com"


# ---------------------------------------------------------------------------
# Full env-driven configuration
# ---------------------------------------------------------------------------


class TestGoogleAuthHelperFullEnvConfig:
    """Tests for end-to-end configuration via environment variables."""

    @pytest.fixture
    def env_configured_auth(self, google_auth_env_restore):
        os.environ["GOOGLE_EMAIL"] = "env@gmail.com"
        os.environ["GOOGLE_PASSWORD"] = "envpass"
        os.environ["GOOGLE_AUTH_DEBUG"] = "1"
        return GoogleAuthHelper()

    def test_env_configured_helper_picks_up_email_from_env(self, env_configured_auth):
        # Arrange
        auth = env_configured_auth
        # Act
        email = auth.email
        # Assert
        assert email == "env@gmail.com"

    def test_env_configured_helper_picks_up_password_from_env(
        self, env_configured_auth
    ):
        # Arrange
        auth = env_configured_auth
        # Act
        password = auth.password
        # Assert
        assert password == "envpass"

    def test_env_configured_helper_picks_up_debug_from_env(self, env_configured_auth):
        # Arrange
        auth = env_configured_auth
        # Act
        debug = auth.debug
        # Assert
        assert debug is True


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__), "-v"])
