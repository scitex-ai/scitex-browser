#!/usr/bin/env python3
"""Tests for ChromeProfileManager class."""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scitex_browser.core.ChromeProfileManager import ChromeProfileManager


class TestChromeProfileManagerConstants:
    """Tests for class constants."""

    def test_extensions_dict_exists_hasattr_chromeprofilemanager_extensions(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert hasattr(ChromeProfileManager, "EXTENSIONS")

    def test_extensions_dict_exists_chromeprofilemanager_extensions_is_dict(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert isinstance(ChromeProfileManager.EXTENSIONS, dict)


    def test_extensions_contains_zotero_zotero_connector_in_chromeprofilemanager_extensions(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert "zotero_connector" in ChromeProfileManager.EXTENSIONS

    def test_extensions_contains_zotero_chromeprofilemanager_extensions_zotero_connector_id_ekhagklc(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert (
            ChromeProfileManager.EXTENSIONS["zotero_connector"]["id"]
            == "ekhagklcjbdpajgpjgmbionohlpdbjgc"
        )


    def test_extensions_contains_lean_library_lean_library_in_chromeprofilemanager_extensions(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert "lean_library" in ChromeProfileManager.EXTENSIONS

    def test_extensions_contains_lean_library_chromeprofilemanager_extensions_lean_library_name_lean_libra(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert ChromeProfileManager.EXTENSIONS["lean_library"]["name"] == "Lean Library"


    def test_extensions_contains_popup_blocker(self):
        """EXTENSIONS should contain Pop-up Blocker."""
        # Arrange
        # Act
        # Assert
        assert "popup_blocker" in ChromeProfileManager.EXTENSIONS

    def test_extensions_contains_accept_cookies(self):
        """EXTENSIONS should contain Accept all cookies."""
        # Arrange
        # Act
        # Assert
        assert "accept_cookies" in ChromeProfileManager.EXTENSIONS

    def test_extensions_contains_captcha_solvers_n_2captcha_solver_in_chromeprofilemanager_extensions(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert "2captcha_solver" in ChromeProfileManager.EXTENSIONS

    def test_extensions_contains_captcha_solvers_captcha_solver_in_chromeprofilemanager_extensions(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert "captcha_solver" in ChromeProfileManager.EXTENSIONS


    def test_available_profile_names_hasattr_chromeprofilemanager_available_profile_names(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert hasattr(ChromeProfileManager, "AVAILABLE_PROFILE_NAMES")

    def test_available_profile_names_chromeprofilemanager_available_profile_names_equals_expected(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        expected = ["system", "extension", "auth", "stealth"]
        # Act
        # Assert
        # Assert
        assert ChromeProfileManager.AVAILABLE_PROFILE_NAMES == expected



class TestChromeProfileManagerInit:
    """Tests for ChromeProfileManager initialization."""

    def test_init_creates_instance(self):
        """Should create instance with profile name."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")
                assert (manager is not None) and (manager.name == 'ChromeProfileManager')

    def test_init_stores_profile_name(self):
        """Should store profile name."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("extension")
                assert manager.profile_name == "extension"

    def test_init_accepts_custom_profile_names(self):
        """Should accept custom profile names (for parallel workers)."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                # Worker profiles for parallel downloads
                manager = ChromeProfileManager("worker_0")
                assert manager.profile_name == "worker_0"

    def test_init_sets_profile_dir(self):
        """Should set profile directory from config."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")
                assert (manager.profile_dir is not None) and (isinstance(manager.profile_dir, Path))

    def test_init_with_chrome_cache_dir(self):
        """Should accept explicit chrome_cache_dir without depending on scholar."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChromeProfileManager("system", chrome_cache_dir=tmpdir)
            assert (manager.profile_dir == Path(tmpdir) / 'system') and (manager.profile_dir.exists())

    def test_no_scholar_dependency_scitex_scholar_not_in_src(self):
        # Arrange
        # Arrange
        import importlib
        mod = importlib.import_module("scitex_browser.core.ChromeProfileManager")
        # Act
        # Act
        src = Path(mod.__file__).read_text()
        # Act
        # Assert
        # Assert
        assert "scitex_scholar" not in src

    def test_no_scholar_dependency_scitex_scholar_not_in_src(self):
        # Arrange
        # Arrange
        import importlib
        mod = importlib.import_module("scitex_browser.core.ChromeProfileManager")
        # Act
        # Act
        src = Path(mod.__file__).read_text()
        # Act
        # Assert
        # Assert
        assert "scitex.scholar" not in src



class TestChromeProfileManagerExtensionStatuses:
    """Tests for _get_extension_statuses method."""

    def test_returns_dict_smoke_case(self):
        """Should return a dictionary."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")
                result = manager._get_extension_statuses(Path(tmpdir))
                assert isinstance(result, dict)

    def test_returns_false_for_missing_extensions_dir(self):
        """Should return False for all when Extensions dir missing."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")
                result = manager._get_extension_statuses(Path(tmpdir))
                # All should be False
                for key in manager.EXTENSIONS:
                    assert result[key] is False

    def test_detects_installed_extension(self):
        """Should detect installed extension with manifest."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")

                # Create fake extension structure
                ext_id = manager.EXTENSIONS["zotero_connector"]["id"]
                ext_path = Path(tmpdir) / "Default" / "Extensions" / ext_id / "1.0.0"
                ext_path.mkdir(parents=True)
                (ext_path / "manifest.json").write_text("{}")

                result = manager._get_extension_statuses(Path(tmpdir))
                assert result["zotero_connector"] is True

    def test_returns_false_for_empty_version_dir(self):
        """Should return False when extension dir exists but no versions."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")

                # Create extension dir without version subdirs
                ext_id = manager.EXTENSIONS["zotero_connector"]["id"]
                ext_path = Path(tmpdir) / "Default" / "Extensions" / ext_id
                ext_path.mkdir(parents=True)

                result = manager._get_extension_statuses(Path(tmpdir))
                assert result["zotero_connector"] is False

    def test_returns_false_for_missing_manifest(self):
        """Should return False when manifest.json is missing."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")

                # Create version dir without manifest
                ext_id = manager.EXTENSIONS["zotero_connector"]["id"]
                ext_path = Path(tmpdir) / "Default" / "Extensions" / ext_id / "1.0.0"
                ext_path.mkdir(parents=True)

                result = manager._get_extension_statuses(Path(tmpdir))
                assert result["zotero_connector"] is False


class TestChromeProfileManagerCheckExtensions:
    """Tests for check_extensions_installed method."""

    def test_returns_bool_smoke_case(self):
        """Should return a boolean."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")
                result = manager.check_extensions_installed(verbose=False)
                assert isinstance(result, bool)

    def test_returns_false_when_no_extensions(self):
        """Should return False when no extensions installed."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")
                result = manager.check_extensions_installed(verbose=False)
                assert result is False

    def test_returns_true_when_all_installed(self):
        """Should return True when all extensions installed."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")

                # Create fake structure for all extensions
                for key, ext_info in manager.EXTENSIONS.items():
                    ext_path = (
                        manager.profile_dir
                        / "Default"
                        / "Extensions"
                        / ext_info["id"]
                        / "1.0.0"
                    )
                    ext_path.mkdir(parents=True)
                    (ext_path / "manifest.json").write_text("{}")

                result = manager.check_extensions_installed(verbose=False)
                assert result is True

    def test_uses_default_profile_dir(self):
        """Should use profile_dir when none provided."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")
                with patch.object(manager, "_get_extension_statuses") as mock:
                    mock.return_value = {}
                    manager.check_extensions_installed(verbose=False)
                    mock.assert_called_once_with(manager.profile_dir)
                    assert mock.called

    def test_accepts_custom_profile_dir(self):
        """Should use custom profile_dir when provided."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")
                custom_dir = Path(tmpdir) / "custom"
                with patch.object(manager, "_get_extension_statuses") as mock:
                    mock.return_value = {}
                    manager.check_extensions_installed(
                        profile_dir=custom_dir, verbose=False
                    )
                    mock.assert_called_once_with(custom_dir)
                    assert mock.called


class TestChromeProfileManagerExtensionPaths:
    """Tests for _get_installed_extension_paths method."""

    def test_returns_list_smoke_case_2(self):
        """Should return a list."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")
                result = manager._get_installed_extension_paths(Path(tmpdir))
                assert isinstance(result, list)

    def test_returns_empty_for_missing_dir(self):
        """Should return empty list when Extensions dir missing."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")
                result = manager._get_installed_extension_paths(Path(tmpdir))
                assert result == []

    def test_returns_paths_for_installed_extensions(self):
        """Should return paths for installed extensions."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")

                # Create fake extension
                ext_id = manager.EXTENSIONS["zotero_connector"]["id"]
                ext_path = Path(tmpdir) / "Default" / "Extensions" / ext_id / "1.0.0"
                ext_path.mkdir(parents=True)
                (ext_path / "manifest.json").write_text("{}")

                result = manager._get_installed_extension_paths(Path(tmpdir))
                assert (len(result) == 1) and (str(ext_path) in result)

    def test_selects_latest_version(self):
        """Should select latest version when multiple exist."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")

                # Create multiple versions
                ext_id = manager.EXTENSIONS["zotero_connector"]["id"]
                for version in ["1.0.0", "2.0.0", "1.5.0"]:
                    ext_path = (
                        Path(tmpdir) / "Default" / "Extensions" / ext_id / version
                    )
                    ext_path.mkdir(parents=True)
                    (ext_path / "manifest.json").write_text("{}")

                result = manager._get_installed_extension_paths(Path(tmpdir))
                assert (len(result) == 1) and ('2.0.0' in result[0])


class TestChromeProfileManagerExtensionArgs:
    """Tests for get_extension_args method."""

    def test_returns_list_smoke_case_2(self):
        """Should return a list."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")
                result = manager.get_extension_args()
                assert isinstance(result, list)

    def test_returns_empty_when_no_extensions(self):
        """Should return empty list when no extensions."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChromeProfileManager(
                "system", chrome_cache_dir=Path(tmpdir) / "chrome"
            )
            result = manager.get_extension_args()
            assert result == []

    def test_returns_extension_args_when_installed(self):
        """Should return proper args when extensions installed."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChromeProfileManager(
                "system", chrome_cache_dir=Path(tmpdir) / "chrome"
            )

            ext_id = manager.EXTENSIONS["zotero_connector"]["id"]
            ext_path = manager.profile_dir / "Default" / "Extensions" / ext_id / "1.0.0"
            ext_path.mkdir(parents=True)
            (ext_path / "manifest.json").write_text("{}")

            result = manager.get_extension_args()
            assert (len(result) > 0) and (any(('--load-extension=' in arg for arg in result))) and (any(('--enable-extensions' in arg for arg in result)))


class TestChromeProfileManagerSyncFromProfile:
    """Tests for sync_from_profile method."""

    def test_returns_false_for_missing_source(self):
        """Should return False when source profile doesn't exist."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChromeProfileManager(
                "test_profile",
                chrome_cache_dir=Path(tmpdir) / "chrome",
            )
            # "source_profile" was never created under chrome_cache_dir.
            result = manager.sync_from_profile("source_profile")
            assert result is False

    def test_creates_target_directory(self):
        """Should create target directory if needed."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                source_dir = Path(tmpdir) / "chrome" / "system"
                source_dir.mkdir(parents=True, exist_ok=True)

                manager = ChromeProfileManager(
                    "new_profile", chrome_cache_dir=Path(tmpdir) / "chrome"
                )

                # Mock rsync to succeed
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        stdout="Number of regular files transferred: 0\nTotal transferred file size: 0 bytes",
                        returncode=0,
                    )
                    result = manager.sync_from_profile("system")
                    assert manager.profile_dir.exists()

    def test_uses_rsync_command(self):
        """Should use rsync with correct arguments."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                source_dir = Path(tmpdir) / "chrome" / "system"
                source_dir.mkdir(parents=True, exist_ok=True)

                manager = ChromeProfileManager(
                    "target", chrome_cache_dir=Path(tmpdir) / "chrome"
                )

                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        stdout="Number of regular files transferred: 0\n", returncode=0
                    )
                    manager.sync_from_profile("system")

                    # Check rsync was called
                    call_args = mock_run.call_args
                    assert ('rsync' in call_args[0][0]) and ('-auv' in call_args[0][0])

    def test_returns_true_on_success(self):
        """Should return True on successful sync."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                source_dir = Path(tmpdir) / "chrome" / "system"
                source_dir.mkdir(parents=True, exist_ok=True)

                manager = ChromeProfileManager(
                    "target", chrome_cache_dir=Path(tmpdir) / "chrome"
                )

                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        stdout="Number of regular files transferred: 10\nTotal transferred file size: 1000 bytes",
                        returncode=0,
                    )
                    result = manager.sync_from_profile("system")
                    assert result is True

    def test_handles_timestamp_errors(self):
        """Should handle 'failed to set times' errors gracefully."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                import subprocess

                source_dir = Path(tmpdir) / "chrome" / "system"
                source_dir.mkdir(parents=True, exist_ok=True)

                manager = ChromeProfileManager(
                    "target", chrome_cache_dir=Path(tmpdir) / "chrome"
                )

                with patch("subprocess.run") as mock_run:
                    error = subprocess.CalledProcessError(23, "rsync")
                    error.stderr = "failed to set times on /some/path"
                    mock_run.side_effect = error
                    result = manager.sync_from_profile("system")
                    # Should still return True for timestamp issues
                    assert result is True


class TestChromeProfileManagerAsync:
    """Tests for async methods."""

    @pytest.mark.asyncio
    async def test_install_extensions_returns_true_when_installed(self):
        """Should return True when extensions already installed."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")

                with patch.object(
                    manager, "check_extensions_installed", return_value=True
                ):
                    result = await manager.install_extensions_manually_if_not_installed_async(
                        verbose=False
                    )
                    assert result is True

    @pytest.mark.asyncio
    async def test_handle_runtime_dialogs_returns_false_on_error(self):
        """Should return False when page operations fail."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")

                # Create mock page that raises error
                mock_page = AsyncMock()
                mock_page.wait_for_timeout.side_effect = Exception("Page closed")

                result = await manager.handle_runtime_extension_dialogs_async(mock_page)
                assert result is False

    @pytest.mark.asyncio
    async def test_handle_runtime_dialogs_clicks_consent_button(self):
        """Should click consent buttons when found."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager = ChromeProfileManager("system")

                # Create mock page with consent button
                mock_element = AsyncMock()
                mock_page = AsyncMock()
                mock_page.wait_for_timeout = AsyncMock()
                mock_page.query_selector = AsyncMock(return_value=mock_element)

                result = await manager.handle_runtime_extension_dialogs_async(mock_page)
                assert result is True
                mock_element.click.assert_called_once()


class TestChromeProfileManagerIntegration:
    """Integration tests for ChromeProfileManager."""

    def test_full_workflow_smoke_case(self):
        """Test complete workflow of creating and checking profile."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                # Create manager
                manager = ChromeProfileManager("test_profile")
                assert (manager.profile_name == 'test_profile') and (manager.check_extensions_installed(verbose=False) is False)

                # Get extension args (should be empty)
                args = manager.get_extension_args()
                assert args == []

                # Create fake extension
                ext_id = manager.EXTENSIONS["zotero_connector"]["id"]
                ext_path = (
                    manager.profile_dir / "Default" / "Extensions" / ext_id / "1.0.0"
                )
                ext_path.mkdir(parents=True)
                (ext_path / "manifest.json").write_text("{}")

                # Now extension args should include it
                args = manager.get_extension_args()
                assert len(args) > 0

    def test_multiple_profiles_independent(self):
        """Multiple profiles should be independent."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SCITEX_DIR": tmpdir}):
                manager1 = ChromeProfileManager("profile1")
                manager2 = ChromeProfileManager("profile2")

                # Different profile dirs
                assert (manager1.profile_dir != manager2.profile_dir) and ('profile1' in str(manager1.profile_dir)) and ('profile2' in str(manager2.profile_dir))


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__), "-v"])
