#!/usr/bin/env python3
"""Tests for ChromeProfileManager class.

History: prior to 2026-05-24 this file used ``unittest.mock`` to patch
``subprocess.run``, to swap ``_get_extension_statuses`` /
``check_extensions_installed`` on live instances, and to fake
``playwright`` Page objects via ``AsyncMock``. Under the no-mocks rule
(PA-306) all of those are now replaced with real collaborators:

- subprocess.run → an executable ``rsync`` shim written into
  ``tmp_path/bin`` and routed via ``PATH``. The shim emits the same
  ``Number of regular files transferred:`` / ``Total transferred file
  size:`` lines that production parses, so the real
  ``subprocess.CompletedProcess`` + ``CalledProcessError`` code paths
  are exercised end-to-end.
- ``_get_extension_statuses`` swap → write real ``manifest.json``
  files into the real profile-extension tree (``tmp_path/.../Default/
  Extensions/<ext_id>/1.0.0/manifest.json``) and observe the real
  return value.
- AsyncMock for Page → hand-rolled ``FakePage`` / ``FakeElement``
  dataclasses exposing only ``wait_for_timeout`` / ``query_selector``
  / ``click``.

Conftest's autouse ``_isolated_chrome_cache`` fixture redirects
``_DEFAULT_CHROME_CACHE`` to a per-test ``tmp_path``, so tests that
don't pass ``chrome_cache_dir=`` still get isolation.
"""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from scitex_browser.core.ChromeProfileManager import ChromeProfileManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _install_manifest(
    profile_dir: Path, ext_id: str, version: str = "1.0.0"
) -> Path:
    """Create a real on-disk ``manifest.json`` under the profile-extension
    tree. Returns the version directory.
    """
    ext_path = profile_dir / "Default" / "Extensions" / ext_id / version
    ext_path.mkdir(parents=True, exist_ok=True)
    (ext_path / "manifest.json").write_text("{}")
    return ext_path


def _install_rsync_shim(
    bin_dir: Path,
    *,
    transferred_files: int = 0,
    total_bytes: int = 0,
    exit_code: int = 0,
    stderr_text: str = "",
) -> Path:
    """Write an executable shell script named ``rsync`` into ``bin_dir``
    that mimics enough of real ``rsync``'s behaviour for
    ``ChromeProfileManager.sync_from_profile`` to parse: emits the two
    ``"Number of regular files transferred"`` / ``"Total transferred
    file size"`` lines production looks for, then exits with
    ``exit_code``.

    Returns the path to the shim binary for debugging.
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    shim = bin_dir / "rsync"
    script = (
        "#!/usr/bin/env bash\n"
        f'echo "Number of regular files transferred: {transferred_files}"\n'
        f'echo "Total transferred file size: {total_bytes} bytes"\n'
    )
    if stderr_text:
        # heredoc-safe single-line stderr
        script += f'echo "{stderr_text}" >&2\n'
    script += f"exit {exit_code}\n"
    shim.write_text(script)
    shim.chmod(
        shim.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    )
    return shim


@pytest.fixture
def path_with_shim(tmp_path):
    """Yield a (bin_dir, restore-state) pair. The fixture prepends
    ``bin_dir`` to ``$PATH`` and restores it on teardown — no
    ``monkeypatch``.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    original_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{bin_dir}{os.pathsep}{original_path}"
    try:
        yield bin_dir
    finally:
        os.environ["PATH"] = original_path


# ---------------------------------------------------------------------------
# Hand-rolled fakes for the playwright Page collaborator
# ---------------------------------------------------------------------------


@dataclass
class FakeElement:
    """Minimal stand-in for a Playwright ``ElementHandle`` exposing only
    ``click()``. Records each click.
    """

    clicks: list[None] = field(default_factory=list)

    async def click(self) -> None:
        self.clicks.append(None)


class FakeConsentPage:
    """Stand-in for a Page that returns a FakeElement for any
    ``query_selector`` call (so the SUT finds a consent button on the
    first selector it tries).
    """

    def __init__(self) -> None:
        self.element = FakeElement()
        self.timeouts: list[int] = []

    async def wait_for_timeout(self, ms: int) -> None:
        self.timeouts.append(ms)

    async def query_selector(self, selector: str):
        return self.element


class FakeFailingPage:
    """Stand-in for a Page whose ``wait_for_timeout`` raises — used to
    exercise the SUT's outer ``except`` branch.
    """

    async def wait_for_timeout(self, ms: int) -> None:
        raise RuntimeError("page closed")

    async def query_selector(self, selector: str):
        raise RuntimeError("page closed")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestChromeProfileManagerExtensionsConstant:
    """Tests for the EXTENSIONS class attribute."""

    def test_extensions_attribute_exists_on_class(self):
        # Arrange
        # Act
        present = hasattr(ChromeProfileManager, "EXTENSIONS")
        # Assert
        assert present is True

    def test_extensions_attribute_is_dict_type(self):
        # Arrange
        # Act
        kind = type(ChromeProfileManager.EXTENSIONS)
        # Assert
        assert kind is dict


@pytest.mark.parametrize(
    "key",
    [
        "zotero_connector",
        "lean_library",
        "popup_blocker",
        "accept_cookies",
        "2captcha_solver",
        "captcha_solver",
    ],
)
def test_extensions_dict_contains_expected_key(key):
    # Arrange
    extensions = ChromeProfileManager.EXTENSIONS
    # Act
    present = key in extensions
    # Assert
    assert present is True


def test_zotero_connector_extension_uses_canonical_chrome_store_id():
    # Arrange
    expected_id = "ekhagklcjbdpajgpjgmbionohlpdbjgc"
    # Act
    actual_id = ChromeProfileManager.EXTENSIONS["zotero_connector"]["id"]
    # Assert
    assert actual_id == expected_id


def test_lean_library_extension_carries_human_readable_name():
    # Arrange
    expected_name = "Lean Library"
    # Act
    actual_name = ChromeProfileManager.EXTENSIONS["lean_library"]["name"]
    # Assert
    assert actual_name == expected_name


class TestChromeProfileManagerAvailableProfileNamesConstant:
    """Tests for the AVAILABLE_PROFILE_NAMES class attribute."""

    def test_available_profile_names_attribute_exists_on_class(self):
        # Arrange
        # Act
        present = hasattr(ChromeProfileManager, "AVAILABLE_PROFILE_NAMES")
        # Assert
        assert present is True

    def test_available_profile_names_matches_expected_list(self):
        # Arrange
        expected = ["system", "extension", "auth", "stealth"]
        # Act
        actual = ChromeProfileManager.AVAILABLE_PROFILE_NAMES
        # Assert
        assert actual == expected


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------


class TestChromeProfileManagerInit:
    """Tests for ChromeProfileManager initialization (uses real tmp_path)."""

    def test_init_assigns_name_to_class_name(self, tmp_path):
        # Arrange
        cache_dir = tmp_path / "chrome"
        # Act
        manager = ChromeProfileManager("system", chrome_cache_dir=cache_dir)
        # Assert
        assert manager.name == "ChromeProfileManager"

    def test_init_stores_supplied_profile_name(self, tmp_path):
        # Arrange
        cache_dir = tmp_path / "chrome"
        # Act
        manager = ChromeProfileManager(
            "extension", chrome_cache_dir=cache_dir
        )
        # Assert
        assert manager.profile_name == "extension"

    def test_init_accepts_arbitrary_worker_style_profile_name(self, tmp_path):
        # Arrange
        cache_dir = tmp_path / "chrome"
        # Act
        manager = ChromeProfileManager(
            "worker_0", chrome_cache_dir=cache_dir
        )
        # Assert
        assert manager.profile_name == "worker_0"

    def test_init_assigns_profile_dir_as_path_instance(self, tmp_path):
        # Arrange
        cache_dir = tmp_path / "chrome"
        # Act
        manager = ChromeProfileManager("system", chrome_cache_dir=cache_dir)
        # Assert
        assert isinstance(manager.profile_dir, Path)

    def test_init_creates_profile_dir_when_chrome_cache_dir_supplied(
        self, tmp_path
    ):
        # Arrange
        cache_dir = tmp_path / "chrome"
        # Act
        manager = ChromeProfileManager("system", chrome_cache_dir=cache_dir)
        # Assert
        assert manager.profile_dir.exists()

    def test_init_places_profile_dir_under_chrome_cache_dir(self, tmp_path):
        # Arrange
        cache_dir = tmp_path / "chrome"
        # Act
        manager = ChromeProfileManager("system", chrome_cache_dir=cache_dir)
        # Assert
        assert manager.profile_dir == cache_dir / "system"


class TestChromeProfileManagerSourceFreeOfScholarDependency:
    """Verify production source no longer imports scitex_scholar."""

    @pytest.fixture
    def production_source(self) -> str:
        import importlib

        mod = importlib.import_module("scitex_browser.core.ChromeProfileManager")
        return Path(mod.__file__).read_text()

    def test_source_does_not_reference_scitex_scholar_module(
        self, production_source
    ):
        # Arrange
        text = production_source
        # Act
        present = "scitex_scholar" in text
        # Assert
        assert present is False

    def test_source_does_not_reference_scitex_dot_scholar_attribute(
        self, production_source
    ):
        # Arrange
        text = production_source
        # Act
        present = "scitex.scholar" in text
        # Assert
        assert present is False


# ---------------------------------------------------------------------------
# _get_extension_statuses (real on-disk manifest files)
# ---------------------------------------------------------------------------


class TestChromeProfileManagerGetExtensionStatuses:
    """Tests for _get_extension_statuses using real filesystem state."""

    @pytest.fixture
    def manager_and_profile(self, tmp_path):
        cache_dir = tmp_path / "chrome"
        manager = ChromeProfileManager("system", chrome_cache_dir=cache_dir)
        return manager, manager.profile_dir

    def test_returns_dict_instance_when_profile_dir_empty(
        self, manager_and_profile
    ):
        # Arrange
        manager, profile_dir = manager_and_profile
        # Act
        result = manager._get_extension_statuses(profile_dir)
        # Assert
        assert isinstance(result, dict)

    def test_returns_all_false_when_extensions_dir_missing(
        self, manager_and_profile
    ):
        # Arrange
        manager, profile_dir = manager_and_profile
        # Act
        result = manager._get_extension_statuses(profile_dir)
        # Assert
        assert all(value is False for value in result.values())

    def test_returns_true_for_extension_with_manifest_on_disk(
        self, manager_and_profile
    ):
        # Arrange
        manager, profile_dir = manager_and_profile
        ext_id = manager.EXTENSIONS["zotero_connector"]["id"]
        _install_manifest(profile_dir, ext_id)
        # Act
        result = manager._get_extension_statuses(profile_dir)
        # Assert
        assert result["zotero_connector"] is True

    def test_returns_false_for_extension_directory_with_no_versions(
        self, manager_and_profile
    ):
        # Arrange
        manager, profile_dir = manager_and_profile
        ext_id = manager.EXTENSIONS["zotero_connector"]["id"]
        (profile_dir / "Default" / "Extensions" / ext_id).mkdir(parents=True)
        # Act
        result = manager._get_extension_statuses(profile_dir)
        # Assert
        assert result["zotero_connector"] is False

    def test_returns_false_for_version_directory_with_no_manifest(
        self, manager_and_profile
    ):
        # Arrange
        manager, profile_dir = manager_and_profile
        ext_id = manager.EXTENSIONS["zotero_connector"]["id"]
        (
            profile_dir / "Default" / "Extensions" / ext_id / "1.0.0"
        ).mkdir(parents=True)
        # Act
        result = manager._get_extension_statuses(profile_dir)
        # Assert
        assert result["zotero_connector"] is False


# ---------------------------------------------------------------------------
# check_extensions_installed
# ---------------------------------------------------------------------------


class TestChromeProfileManagerCheckExtensionsInstalled:
    """Tests for check_extensions_installed using real filesystem state."""

    @pytest.fixture
    def manager(self, tmp_path) -> ChromeProfileManager:
        return ChromeProfileManager(
            "system", chrome_cache_dir=tmp_path / "chrome"
        )

    def test_returns_bool_type_when_profile_dir_empty(self, manager):
        # Arrange
        # Act
        result = manager.check_extensions_installed(verbose=False)
        # Assert
        assert isinstance(result, bool)

    def test_returns_false_when_no_extensions_on_disk(self, manager):
        # Arrange
        # Act
        result = manager.check_extensions_installed(verbose=False)
        # Assert
        assert result is False

    def test_returns_true_when_all_extensions_have_manifest_on_disk(
        self, manager
    ):
        # Arrange
        for ext_info in manager.EXTENSIONS.values():
            _install_manifest(manager.profile_dir, ext_info["id"])
        # Act
        result = manager.check_extensions_installed(verbose=False)
        # Assert
        assert result is True

    def test_default_profile_dir_query_returns_false_when_empty(self, manager):
        # Arrange
        # (no extensions installed)
        # Act
        result = manager.check_extensions_installed(verbose=False)
        # Assert
        assert result is False

    def test_custom_profile_dir_overrides_default_for_lookup(
        self, manager, tmp_path
    ):
        # Arrange
        custom = tmp_path / "custom"
        custom.mkdir()
        # Act
        result = manager.check_extensions_installed(
            profile_dir=custom, verbose=False
        )
        # Assert
        assert result is False


# ---------------------------------------------------------------------------
# _get_installed_extension_paths
# ---------------------------------------------------------------------------


class TestChromeProfileManagerInstalledExtensionPaths:
    """Tests for _get_installed_extension_paths using real on-disk state."""

    @pytest.fixture
    def manager(self, tmp_path) -> ChromeProfileManager:
        return ChromeProfileManager(
            "system", chrome_cache_dir=tmp_path / "chrome"
        )

    def test_returns_list_type_when_profile_dir_empty(self, manager):
        # Arrange
        # Act
        result = manager._get_installed_extension_paths(manager.profile_dir)
        # Assert
        assert isinstance(result, list)

    def test_returns_empty_list_when_extensions_dir_missing(self, manager):
        # Arrange
        # Act
        result = manager._get_installed_extension_paths(manager.profile_dir)
        # Assert
        assert result == []

    def test_returns_path_for_each_installed_extension(self, manager):
        # Arrange
        ext_id = manager.EXTENSIONS["zotero_connector"]["id"]
        _install_manifest(manager.profile_dir, ext_id)
        # Act
        result = manager._get_installed_extension_paths(manager.profile_dir)
        # Assert
        assert len(result) == 1

    def test_selects_latest_semver_version_directory(self, manager):
        # Arrange
        ext_id = manager.EXTENSIONS["zotero_connector"]["id"]
        for version in ("1.0.0", "2.0.0", "1.5.0"):
            _install_manifest(manager.profile_dir, ext_id, version=version)
        # Act
        result = manager._get_installed_extension_paths(manager.profile_dir)
        # Assert
        assert result[0].endswith("2.0.0")


# ---------------------------------------------------------------------------
# get_extension_args
# ---------------------------------------------------------------------------


class TestChromeProfileManagerGetExtensionArgs:
    """Tests for get_extension_args using real on-disk state."""

    @pytest.fixture
    def manager(self, tmp_path) -> ChromeProfileManager:
        return ChromeProfileManager(
            "system", chrome_cache_dir=tmp_path / "chrome"
        )

    def test_returns_list_type_when_no_extensions_installed(self, manager):
        # Arrange
        # Act
        result = manager.get_extension_args()
        # Assert
        assert isinstance(result, list)

    def test_returns_empty_list_when_no_extensions_installed(self, manager):
        # Arrange
        # Act
        result = manager.get_extension_args()
        # Assert
        assert result == []

    @pytest.fixture
    def manager_with_one_installed_extension(self, manager):
        ext_id = manager.EXTENSIONS["zotero_connector"]["id"]
        _install_manifest(manager.profile_dir, ext_id)
        return manager

    def test_returns_non_empty_args_when_extension_installed(
        self, manager_with_one_installed_extension
    ):
        # Arrange
        mgr = manager_with_one_installed_extension
        # Act
        result = mgr.get_extension_args()
        # Assert
        assert len(result) > 0

    def test_args_include_load_extension_flag(
        self, manager_with_one_installed_extension
    ):
        # Arrange
        mgr = manager_with_one_installed_extension
        # Act
        result = mgr.get_extension_args()
        # Assert
        assert any("--load-extension=" in arg for arg in result)

    def test_args_include_enable_extensions_flag(
        self, manager_with_one_installed_extension
    ):
        # Arrange
        mgr = manager_with_one_installed_extension
        # Act
        result = mgr.get_extension_args()
        # Assert
        assert any("--enable-extensions" in arg for arg in result)


# ---------------------------------------------------------------------------
# sync_from_profile (uses real rsync shim)
# ---------------------------------------------------------------------------


class TestChromeProfileManagerSyncFromProfile:
    """Tests for sync_from_profile against a real rsync shim in tmp_path."""

    def test_returns_false_when_source_profile_does_not_exist(self, tmp_path):
        # Arrange
        cache_dir = tmp_path / "chrome"
        manager = ChromeProfileManager(
            "test_profile", chrome_cache_dir=cache_dir
        )
        # Act
        result = manager.sync_from_profile("source_profile")
        # Assert
        assert result is False

    def test_creates_target_profile_directory_on_sync(
        self, tmp_path, path_with_shim
    ):
        # Arrange
        cache_dir = tmp_path / "chrome"
        (cache_dir / "system").mkdir(parents=True)
        _install_rsync_shim(path_with_shim, transferred_files=0, total_bytes=0)
        manager = ChromeProfileManager(
            "new_profile", chrome_cache_dir=cache_dir
        )
        # Act
        manager.sync_from_profile("system")
        # Assert
        assert manager.profile_dir.exists()

    def test_sync_invokes_real_rsync_executable_via_path(
        self, tmp_path, path_with_shim
    ):
        # Arrange
        cache_dir = tmp_path / "chrome"
        (cache_dir / "system").mkdir(parents=True)
        # Shim with a sentinel file count so we know it ran end-to-end
        _install_rsync_shim(
            path_with_shim, transferred_files=7, total_bytes=2048
        )
        manager = ChromeProfileManager(
            "target", chrome_cache_dir=cache_dir
        )
        # Act
        result = manager.sync_from_profile("system")
        # Assert
        assert result is True

    def test_sync_returns_true_when_rsync_reports_zero_transfers(
        self, tmp_path, path_with_shim
    ):
        # Arrange
        cache_dir = tmp_path / "chrome"
        (cache_dir / "system").mkdir(parents=True)
        _install_rsync_shim(
            path_with_shim, transferred_files=0, total_bytes=0
        )
        manager = ChromeProfileManager(
            "target", chrome_cache_dir=cache_dir
        )
        # Act
        result = manager.sync_from_profile("system")
        # Assert
        assert result is True

    def test_sync_returns_true_on_rsync_exit23_timestamp_only_failure(
        self, tmp_path, path_with_shim
    ):
        # Arrange
        cache_dir = tmp_path / "chrome"
        (cache_dir / "system").mkdir(parents=True)
        _install_rsync_shim(
            path_with_shim,
            exit_code=23,
            stderr_text="rsync: failed to set times on /some/path",
        )
        manager = ChromeProfileManager(
            "target", chrome_cache_dir=cache_dir
        )
        # Act
        result = manager.sync_from_profile("system")
        # Assert
        assert result is True


# ---------------------------------------------------------------------------
# install_extensions_manually_if_not_installed_async (filesystem-only)
# ---------------------------------------------------------------------------


class TestChromeProfileManagerInstallExtensionsAsync:
    """Tests for install_extensions_manually_if_not_installed_async."""

    @pytest.mark.asyncio
    async def test_returns_true_when_all_extensions_already_on_disk(
        self, tmp_path
    ):
        # Arrange
        cache_dir = tmp_path / "chrome"
        manager = ChromeProfileManager("system", chrome_cache_dir=cache_dir)
        for ext_info in manager.EXTENSIONS.values():
            _install_manifest(manager.profile_dir, ext_info["id"])
        # Act
        result = await manager.install_extensions_manually_if_not_installed_async(
            verbose=False
        )
        # Assert
        assert result is True


# ---------------------------------------------------------------------------
# handle_runtime_extension_dialogs_async (uses hand-rolled FakePage)
# ---------------------------------------------------------------------------


class TestChromeProfileManagerHandleRuntimeDialogsAsync:
    """Tests for handle_runtime_extension_dialogs_async with hand-rolled fakes."""

    @pytest.fixture
    def manager(self, tmp_path) -> ChromeProfileManager:
        return ChromeProfileManager(
            "system", chrome_cache_dir=tmp_path / "chrome"
        )

    @pytest.mark.asyncio
    async def test_returns_false_when_page_wait_raises(self, manager):
        # Arrange
        page = FakeFailingPage()
        # Act
        result = await manager.handle_runtime_extension_dialogs_async(page)
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_when_consent_button_found_and_clicked(
        self, manager
    ):
        # Arrange
        page = FakeConsentPage()
        # Act
        result = await manager.handle_runtime_extension_dialogs_async(page)
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_clicks_consent_button_exactly_once(self, manager):
        # Arrange
        page = FakeConsentPage()
        # Act
        await manager.handle_runtime_extension_dialogs_async(page)
        # Assert
        assert len(page.element.clicks) == 1


# ---------------------------------------------------------------------------
# Multi-profile independence
# ---------------------------------------------------------------------------


class TestChromeProfileManagerMultipleProfilesIndependent:
    """Multiple manager instances should target distinct on-disk dirs."""

    @pytest.fixture
    def two_managers(self, tmp_path):
        cache_dir = tmp_path / "chrome"
        return (
            ChromeProfileManager("profile1", chrome_cache_dir=cache_dir),
            ChromeProfileManager("profile2", chrome_cache_dir=cache_dir),
        )

    def test_profile_dirs_differ_across_instances(self, two_managers):
        # Arrange
        m1, m2 = two_managers
        # Act
        same = m1.profile_dir == m2.profile_dir
        # Assert
        assert same is False

    def test_first_manager_profile_dir_contains_its_profile_name(
        self, two_managers
    ):
        # Arrange
        m1, _ = two_managers
        # Act
        contained = "profile1" in str(m1.profile_dir)
        # Assert
        assert contained is True

    def test_second_manager_profile_dir_contains_its_profile_name(
        self, two_managers
    ):
        # Arrange
        _, m2 = two_managers
        # Act
        contained = "profile2" in str(m2.profile_dir)
        # Assert
        assert contained is True


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__), "-v"])
