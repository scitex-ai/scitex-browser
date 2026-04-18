"""Shared pytest fixtures for scitex-browser tests."""

import pytest


@pytest.fixture(autouse=True)
def _isolated_chrome_cache(monkeypatch, tmp_path):
    """Redirect ChromeProfileManager default cache dir to a per-test tmp dir.

    Without this, tests that call ``ChromeProfileManager(profile_name)`` without
    ``chrome_cache_dir`` leak into ``~/.cache/scitex_browser/chrome`` and
    accumulate state across runs.
    """
    cache_dir = tmp_path / "chrome_cache"
    cache_dir.mkdir()
    import importlib

    mod = importlib.import_module("scitex_browser.core.ChromeProfileManager")
    monkeypatch.setattr(mod, "_DEFAULT_CHROME_CACHE", cache_dir)
    yield cache_dir
