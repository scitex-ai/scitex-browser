#!/usr/bin/env python3
"""Tests for GoogleAuthHelper class."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scitex_browser.auth.google import GoogleAuthHelper, google_login


class TestGoogleAuthHelperInit:
    """Tests for GoogleAuthHelper initialization."""

    def test_init_creates_instance(self):
        """GoogleAuthHelper should initialize without errors."""
        # Arrange
        # Act
        auth = GoogleAuthHelper()
        # Assert
        assert auth is not None

    def test_init_stores_email(self):
        """Should store provided email."""
        # Arrange
        # Act
        auth = GoogleAuthHelper(email="test@gmail.com")
        # Assert
        assert auth.email == "test@gmail.com"

    def test_init_stores_password(self):
        """Should store provided password."""
        # Arrange
        # Act
        auth = GoogleAuthHelper(password="secret123")
        # Assert
        assert auth.password == "secret123"

    def test_init_stores_debug_flag(self):
        """Should store debug flag."""
        # Arrange
        # Act
        auth = GoogleAuthHelper(debug=True)
        # Assert
        assert auth.debug is True

    def test_init_uses_env_email_when_not_provided(self):
        """Should use GOOGLE_EMAIL env var when email not provided."""
        # Arrange
        # Act
        # Assert
        with patch.dict(os.environ, {"GOOGLE_EMAIL": "env@gmail.com"}):
            auth = GoogleAuthHelper()
            assert auth.email == "env@gmail.com"

    def test_init_uses_env_password_when_not_provided(self):
        """Should use GOOGLE_PASSWORD env var when password not provided."""
        # Arrange
        # Act
        # Assert
        with patch.dict(os.environ, {"GOOGLE_PASSWORD": "envpass"}):
            auth = GoogleAuthHelper()
            assert auth.password == "envpass"

    def test_init_uses_env_debug_when_not_provided(self):
        """Should use GOOGLE_AUTH_DEBUG env var when debug not provided."""
        # Arrange
        # Act
        # Assert
        with patch.dict(os.environ, {"GOOGLE_AUTH_DEBUG": "1"}):
            auth = GoogleAuthHelper()
            assert auth.debug is True

    def test_init_prefers_param_over_env(self):
        """Provided params should override env vars."""
        # Arrange
        # Act
        # Assert
        with patch.dict(
            os.environ, {"GOOGLE_EMAIL": "env@gmail.com", "GOOGLE_PASSWORD": "envpass"}
        ):
            auth = GoogleAuthHelper(email="param@gmail.com", password="parampass")
            assert (auth.email == 'param@gmail.com') and (auth.password == 'parampass')

    def test_init_defaults_to_empty_strings(self):
        """Should default to empty strings when nothing provided."""
        # Arrange
        # Act
        # Assert
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GOOGLE_EMAIL", None)
            os.environ.pop("GOOGLE_PASSWORD", None)
            os.environ.pop("GOOGLE_AUTH_DEBUG", None)
            auth = GoogleAuthHelper()
            assert (auth.email == '') and (auth.password == '') and (auth.debug is False)


class TestGoogleAuthHelperLog:
    """Tests for _log method."""

    def test_log_prints_when_debug_enabled_test_message_in_captured_err(self, capsys):
        # Arrange
        # Arrange
        auth = GoogleAuthHelper(debug=True)
        auth._log("Test message")
        # Act
        # Act
        captured = capsys.readouterr()
        # Act
        # Assert
        # Assert
        assert "Test message" in captured.err

    def test_log_prints_when_debug_enabled_googleauth_in_captured_err(self, capsys):
        # Arrange
        # Arrange
        auth = GoogleAuthHelper(debug=True)
        auth._log("Test message")
        # Act
        # Act
        captured = capsys.readouterr()
        # Act
        # Assert
        # Assert
        assert "[GoogleAuth]" in captured.err


    def test_log_silent_when_debug_disabled(self, capsys):
        """_log should not print when debug is False."""
        # Arrange
        auth = GoogleAuthHelper(debug=False)
        auth._log("Test message")
        # Act
        captured = capsys.readouterr()
        # Assert
        assert captured.err == ""


class TestLoginViaGoogleButton:
    """Tests for login_via_google_button method."""

    @pytest.mark.asyncio
    async def test_returns_false_when_button_not_found(self):
        """Should return False when Google button not found."""
        # Arrange
        auth = GoogleAuthHelper()
        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(return_value=None)

        # Act
        result = await auth.login_via_google_button(mock_page)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_tries_alternative_selectors(self):
        """Should try alternative selectors when primary fails."""
        # Arrange
        auth = GoogleAuthHelper()
        mock_page = MagicMock()
        # First call fails, second succeeds
        call_count = 0

        async def mock_query_selector(selector):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                return MagicMock()
            return None

        mock_page.query_selector = mock_query_selector
        mock_page.context.expect_page = MagicMock()

        # This will fail due to other issues but tests selector logic
        # Act
        result = await auth.login_via_google_button(mock_page)

        # Assert
        assert call_count >= 2

    @pytest.mark.asyncio
    async def test_handles_exception_gracefully(self):
        """Should return False on exception."""
        # Arrange
        auth = GoogleAuthHelper()
        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(side_effect=Exception("Test error"))

        # Act
        result = await auth.login_via_google_button(mock_page)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_clicks_google_button(self):
        """Should click the Google button when found."""
        # Arrange
        # Act
        # Assert
        auth = GoogleAuthHelper()
        mock_page = MagicMock()
        mock_button = MagicMock()
        mock_button.click = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=mock_button)

        # Setup popup context manager
        mock_popup = MagicMock()
        mock_popup.url = "https://accounts.google.com"
        mock_popup_info = MagicMock()
        mock_popup_info.value = mock_popup

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_popup_info)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_page.context.expect_page = MagicMock(return_value=mock_cm)

        # Mock popup handler
        with patch.object(auth, "_handle_google_popup", AsyncMock(return_value=False)):
            await auth.login_via_google_button(mock_page)
            mock_button.click.assert_called_once()
            assert mock_button.click.call_count == 1


class TestHandleGooglePopup:
    """Tests for _handle_google_popup method."""

    @pytest.mark.asyncio
    async def test_returns_false_on_email_failure(self):
        """Should return False when email fill fails."""
        # Arrange
        # Act
        # Assert
        auth = GoogleAuthHelper()
        mock_popup = MagicMock()
        mock_popup.wait_for_load_state = AsyncMock()
        mock_popup.wait_for_timeout = AsyncMock()

        with patch.object(auth, "_fill_email", AsyncMock(return_value=False)):
            result = await auth._handle_google_popup(mock_popup)
            assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_password_failure(self):
        """Should return False when password fill fails."""
        # Arrange
        # Act
        # Assert
        auth = GoogleAuthHelper()
        mock_popup = MagicMock()
        mock_popup.wait_for_load_state = AsyncMock()
        mock_popup.wait_for_timeout = AsyncMock()

        with patch.object(auth, "_fill_email", AsyncMock(return_value=True)):
            with patch.object(auth, "_fill_password", AsyncMock(return_value=False)):
                result = await auth._handle_google_popup(mock_popup)
                assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_when_popup_closes(self):
        """Should return True when popup closes (indicates success)."""
        # Arrange
        # Act
        # Assert
        auth = GoogleAuthHelper()
        mock_popup = MagicMock()
        mock_popup.wait_for_load_state = AsyncMock()
        mock_popup.wait_for_timeout = AsyncMock()
        mock_popup.wait_for_event = AsyncMock(return_value=None)

        with patch.object(auth, "_fill_email", AsyncMock(return_value=True)):
            with patch.object(auth, "_fill_password", AsyncMock(return_value=True)):
                result = await auth._handle_google_popup(mock_popup)
                assert result is True

    @pytest.mark.asyncio
    async def test_handles_exception_gracefully(self):
        """Should return False on exception."""
        # Arrange
        auth = GoogleAuthHelper()
        mock_popup = MagicMock()
        mock_popup.wait_for_load_state = AsyncMock(side_effect=Exception("Load error"))

        # Act
        result = await auth._handle_google_popup(mock_popup)
        # Assert
        assert result is False


class TestFillEmail:
    """Tests for _fill_email method."""

    @pytest.mark.asyncio
    async def test_fills_email_input(self):
        """Should fill email in input field."""
        # Arrange
        auth = GoogleAuthHelper(email="test@gmail.com")
        mock_popup = MagicMock()
        mock_popup.wait_for_selector = AsyncMock()
        mock_popup.fill = AsyncMock()
        mock_popup.wait_for_timeout = AsyncMock()

        mock_next_btn = MagicMock()
        mock_next_btn.click = AsyncMock()
        mock_popup.query_selector = AsyncMock(return_value=mock_next_btn)

        result = await auth._fill_email(mock_popup)

        # Act
        mock_popup.fill.assert_called_with('input[type="email"]', "test@gmail.com")
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_clicks_next_button(self):
        """Should click Next button after filling email."""
        # Arrange
        # Act
        # Assert
        auth = GoogleAuthHelper(email="test@gmail.com")
        mock_popup = MagicMock()
        mock_popup.wait_for_selector = AsyncMock()
        mock_popup.fill = AsyncMock()
        mock_popup.wait_for_timeout = AsyncMock()

        mock_next_btn = MagicMock()
        mock_next_btn.click = AsyncMock()
        mock_popup.query_selector = AsyncMock(return_value=mock_next_btn)

        await auth._fill_email(mock_popup)

        mock_next_btn.click.assert_called_once()
        assert mock_next_btn.click.call_count == 1

    @pytest.mark.asyncio
    async def test_returns_false_when_next_button_not_found(self):
        """Should return False when Next button not found."""
        # Arrange
        auth = GoogleAuthHelper(email="test@gmail.com")
        mock_popup = MagicMock()
        mock_popup.wait_for_selector = AsyncMock()
        mock_popup.fill = AsyncMock()
        mock_popup.wait_for_timeout = AsyncMock()
        mock_popup.query_selector = AsyncMock(return_value=None)

        # Act
        result = await auth._fill_email(mock_popup)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_handles_exception_gracefully(self):
        """Should return False on exception."""
        # Arrange
        auth = GoogleAuthHelper(email="test@gmail.com")
        mock_popup = MagicMock()
        mock_popup.wait_for_selector = AsyncMock(
            side_effect=Exception("Selector error")
        )

        # Act
        result = await auth._fill_email(mock_popup)

        # Assert
        assert result is False


class TestFillPassword:
    """Tests for _fill_password method."""

    @pytest.mark.asyncio
    async def test_fills_password_input(self):
        """Should fill password in input field."""
        # Arrange
        auth = GoogleAuthHelper(password="secret123")
        mock_popup = MagicMock()
        mock_popup.wait_for_selector = AsyncMock()
        mock_popup.fill = AsyncMock()
        mock_popup.wait_for_timeout = AsyncMock()

        mock_next_btn = MagicMock()
        mock_next_btn.click = AsyncMock()
        mock_popup.query_selector = AsyncMock(return_value=mock_next_btn)

        with patch.object(auth, "_wait_for_2fa", AsyncMock(return_value=True)):
            with patch.object(auth, "_handle_consent_screens", AsyncMock()):
                result = await auth._fill_password(mock_popup)

        # Act
        mock_popup.fill.assert_called_with('input[type="password"]', "secret123")
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_next_button_not_found(self):
        """Should return False when Next button not found."""
        # Arrange
        auth = GoogleAuthHelper(password="secret123")
        mock_popup = MagicMock()
        mock_popup.wait_for_selector = AsyncMock()
        mock_popup.fill = AsyncMock()
        mock_popup.wait_for_timeout = AsyncMock()
        mock_popup.query_selector = AsyncMock(return_value=None)

        # Act
        result = await auth._fill_password(mock_popup)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_calls_2fa_handler(self):
        """Should call 2FA handler after password."""
        # Arrange
        # Act
        # Assert
        auth = GoogleAuthHelper(password="secret123")
        mock_popup = MagicMock()
        mock_popup.wait_for_selector = AsyncMock()
        mock_popup.fill = AsyncMock()
        mock_popup.wait_for_timeout = AsyncMock()

        mock_next_btn = MagicMock()
        mock_next_btn.click = AsyncMock()
        mock_popup.query_selector = AsyncMock(return_value=mock_next_btn)

        mock_2fa = AsyncMock(return_value=True)
        with patch.object(auth, "_wait_for_2fa", mock_2fa):
            with patch.object(auth, "_handle_consent_screens", AsyncMock()):
                await auth._fill_password(mock_popup)

        mock_2fa.assert_called_once()
        assert mock_2fa.call_count == 1

    @pytest.mark.asyncio
    async def test_returns_false_when_2fa_fails(self):
        """Should return False when 2FA fails."""
        # Arrange
        auth = GoogleAuthHelper(password="secret123")
        mock_popup = MagicMock()
        mock_popup.wait_for_selector = AsyncMock()
        mock_popup.fill = AsyncMock()
        mock_popup.wait_for_timeout = AsyncMock()

        mock_next_btn = MagicMock()
        mock_next_btn.click = AsyncMock()
        mock_popup.query_selector = AsyncMock(return_value=mock_next_btn)

        # Act
        with patch.object(auth, "_wait_for_2fa", AsyncMock(return_value=False)):
            result = await auth._fill_password(mock_popup)

        # Assert
        assert result is False


class TestHandleConsentScreens:
    """Tests for _handle_consent_screens method."""

    @pytest.mark.asyncio
    async def test_clicks_continue_button(self):
        """Should click Continue button when found."""
        # Arrange
        # Act
        # Assert
        auth = GoogleAuthHelper()
        mock_popup = MagicMock()

        mock_btn = MagicMock()
        mock_btn.is_visible = AsyncMock(return_value=True)
        mock_btn.click = AsyncMock()
        mock_popup.query_selector = AsyncMock(return_value=mock_btn)
        mock_popup.wait_for_timeout = AsyncMock()

        await auth._handle_consent_screens(mock_popup)

        mock_btn.click.assert_called_once()
        assert mock_btn.click.call_count == 1

    @pytest.mark.asyncio
    async def test_handles_no_consent_screen(self):
        """Should handle case when no consent screen present."""
        # Arrange
        # Act
        # Assert
        auth = GoogleAuthHelper()
        mock_popup = MagicMock()
        mock_popup.query_selector = AsyncMock(return_value=None)

        # Should not raise
        await auth._handle_consent_screens(mock_popup)

    @pytest.mark.asyncio
    async def test_handles_exception_gracefully(self):
        """Should handle exceptions gracefully."""
        # Arrange
        # Act
        # Assert
        auth = GoogleAuthHelper()
        mock_popup = MagicMock()
        mock_popup.query_selector = AsyncMock(side_effect=Exception("Error"))

        # Should not raise
        await auth._handle_consent_screens(mock_popup)


class TestWaitFor2FA:
    """Tests for _wait_for_2fa method."""

    @pytest.mark.asyncio
    async def test_returns_true_when_not_2fa_page(self):
        """Should return True when not on 2FA page."""
        # Arrange
        auth = GoogleAuthHelper()
        mock_popup = MagicMock()
        mock_popup.inner_text = AsyncMock(return_value="Welcome to Google")

        # Act
        result = await auth._wait_for_2fa(mock_popup)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_detects_2fa_indicators(self):
        """Should detect 2FA indicators in page text."""
        # Arrange
        auth = GoogleAuthHelper()
        mock_popup = MagicMock()
        mock_popup.inner_text = AsyncMock(return_value="2-Step Verification required")
        mock_popup.url = "https://accounts.google.com/2fa"
        mock_popup.wait_for_timeout = AsyncMock()

        # Simulate popup closing
        call_count = 0

        @property
        def url_getter():
            nonlocal call_count
            call_count += 1
            if call_count > 2:
                raise Exception("Popup closed")
            return "https://accounts.google.com/2fa"

        type(mock_popup).url = url_getter

        # Act
        result = await auth._wait_for_2fa(mock_popup, timeout=5000)

        # Should have detected 2FA
        # Assert
        assert mock_popup.inner_text.called

    @pytest.mark.asyncio
    async def test_handles_exception_gracefully(self):
        """Should return False on exception."""
        # Arrange
        auth = GoogleAuthHelper()
        mock_popup = MagicMock()
        mock_popup.inner_text = AsyncMock(side_effect=Exception("Error"))

        # Act
        result = await auth._wait_for_2fa(mock_popup)

        # Assert
        assert result is False


class TestIsLoggedIn:
    """Tests for is_logged_in method."""

    @pytest.mark.asyncio
    async def test_returns_false_for_login_url(self):
        """Should return False when URL contains login."""
        # Arrange
        auth = GoogleAuthHelper()
        mock_page = MagicMock()
        mock_page.url = "https://example.com/login"

        # Act
        result = await auth.is_logged_in(mock_page)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_for_signin_url(self):
        """Should return False when URL contains signin."""
        # Arrange
        auth = GoogleAuthHelper()
        mock_page = MagicMock()
        mock_page.url = "https://example.com/signin"

        # Act
        result = await auth.is_logged_in(mock_page)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_for_oauth_url(self):
        """Should return False when URL contains oauth."""
        # Arrange
        auth = GoogleAuthHelper()
        mock_page = MagicMock()
        mock_page.url = "https://example.com/oauth/authorize"

        # Act
        result = await auth.is_logged_in(mock_page)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_for_google_accounts_url(self):
        """Should return False when URL is Google accounts."""
        # Arrange
        auth = GoogleAuthHelper()
        mock_page = MagicMock()
        mock_page.url = "https://accounts.google.com/signin"

        # Act
        result = await auth.is_logged_in(mock_page)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_for_dashboard_url(self):
        """Should return True when URL suggests logged in."""
        # Arrange
        auth = GoogleAuthHelper()
        mock_page = MagicMock()
        mock_page.url = "https://example.com/dashboard"

        # Act
        result = await auth.is_logged_in(mock_page)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_accepts_custom_indicators(self):
        """Should use custom login indicators."""
        # Arrange
        auth = GoogleAuthHelper()
        mock_page = MagicMock()
        mock_page.url = "https://example.com/auth"

        # Act
        result = await auth.is_logged_in(mock_page, login_indicators=["auth"])

        # Assert
        assert result is False


class TestGoogleLoginConvenienceFunction:
    """Tests for google_login convenience function."""

    @pytest.mark.asyncio
    async def test_creates_auth_helper(self):
        """Should create GoogleAuthHelper with correct params."""
        # Arrange
        # Act
        # Assert
        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(return_value=None)

        with patch("scitex_browser.auth.google.GoogleAuthHelper") as mock_class:
            mock_instance = MagicMock()
            mock_instance.login_via_google_button = AsyncMock(return_value=True)
            mock_class.return_value = mock_instance

            await google_login(mock_page, "test@gmail.com", "password", debug=True)

            mock_class.assert_called_with(
                email="test@gmail.com", password="password", debug=True
            )
            assert mock_class.called

    @pytest.mark.asyncio
    async def test_calls_login_method(self):
        """Should call login_via_google_button method."""
        # Arrange
        # Act
        # Assert
        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(return_value=None)

        with patch("scitex_browser.auth.google.GoogleAuthHelper") as mock_class:
            mock_instance = MagicMock()
            mock_instance.login_via_google_button = AsyncMock(return_value=True)
            mock_class.return_value = mock_instance

            result = await google_login(
                mock_page, "test@gmail.com", "password", button_selector="custom"
            )

            mock_instance.login_via_google_button.assert_called_with(
                mock_page, "custom"
            )
            assert result is True


class TestGoogleAuthHelperIntegration:
    """Integration tests for GoogleAuthHelper."""

    def test_multiple_instances_independent_auth1_email_auth2_email(self):
        # Arrange
        # Arrange
        auth1 = GoogleAuthHelper(email="user1@gmail.com")
        # Act
        # Act
        auth2 = GoogleAuthHelper(email="user2@gmail.com")
        # Act
        # Assert
        # Assert
        assert auth1.email != auth2.email

    def test_multiple_instances_independent_auth1_email_equals_user1_gmail_com(self):
        # Arrange
        # Arrange
        auth1 = GoogleAuthHelper(email="user1@gmail.com")
        # Act
        # Act
        auth2 = GoogleAuthHelper(email="user2@gmail.com")
        # Act
        # Assert
        # Assert
        assert auth1.email == "user1@gmail.com"

    def test_multiple_instances_independent_auth2_email_equals_user2_gmail_com(self):
        # Arrange
        # Arrange
        auth1 = GoogleAuthHelper(email="user1@gmail.com")
        # Act
        # Act
        auth2 = GoogleAuthHelper(email="user2@gmail.com")
        # Act
        # Assert
        # Assert
        assert auth2.email == "user2@gmail.com"


    def test_full_config_from_env(self):
        """Should configure fully from environment."""
        # Arrange
        # Act
        # Assert
        with patch.dict(
            os.environ,
            {
                "GOOGLE_EMAIL": "env@gmail.com",
                "GOOGLE_PASSWORD": "envpass",
                "GOOGLE_AUTH_DEBUG": "1",
            },
        ):
            auth = GoogleAuthHelper()
            assert (auth.email == 'env@gmail.com') and (auth.password == 'envpass') and (auth.debug is True)


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__), "-v"])
