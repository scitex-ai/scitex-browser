"""Shared pytest fixtures for scitex-browser tests.

Subprocess coverage is configured in pyproject.toml via coverage.py's subprocess patch; test collection must not install .pth files or overwrite caller-owned coverage environment variables.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _isolated_chrome_cache(tmp_path):
    """Redirect ChromeProfileManager default cache dir to a per-test tmp dir.

    Without this, tests that call ``ChromeProfileManager(profile_name)`` without
    ``chrome_cache_dir`` leak into ``~/.cache/scitex_browser/chrome`` and
    accumulate state across runs.

    Snapshots and restores ``_DEFAULT_CHROME_CACHE`` on the module rather than
    using ``monkeypatch`` — no mocks, no fixture-parameter mocking.
    """
    cache_dir = tmp_path / "chrome_cache"
    cache_dir.mkdir()
    import importlib

    mod = importlib.import_module("scitex_browser.core.ChromeProfileManager")
    original = mod._DEFAULT_CHROME_CACHE
    mod._DEFAULT_CHROME_CACHE = cache_dir
    try:
        yield cache_dir
    finally:
        mod._DEFAULT_CHROME_CACHE = original
