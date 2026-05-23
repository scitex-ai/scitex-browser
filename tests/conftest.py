"""Shared pytest fixtures for scitex-browser tests.

Also wires module-import-time subprocess coverage (parallel +
COVERAGE_PROCESS_START + .pth shim) so coverage from child
Python interpreters (subprocess.run, etc.) is captured. See
``05_development_06_subprocess-coverage.md`` for rationale.
"""

from __future__ import annotations

import os
import sysconfig
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Force-set (NOT setdefault): pytest-cov has already set COVERAGE_FILE
# to a per-test tmp dir by the time conftest is loaded, so setdefault
# would be a silent no-op.
os.environ["COVERAGE_PROCESS_START"] = str(_PROJECT_ROOT / "pyproject.toml")
os.environ["COVERAGE_FILE"] = str(_PROJECT_ROOT / ".coverage")


def _ensure_subprocess_coverage_shim() -> None:
    """Drop an idempotent ``.pth`` file in site-packages that auto-starts
    coverage in every child Python interpreter via
    ``coverage.process_startup()``.
    """
    purelib = Path(sysconfig.get_paths()["purelib"])
    pth = purelib / "_scitex_browser_subprocess_coverage.pth"
    shim = (
        "import os, coverage\n"
        "if os.environ.get('COVERAGE_PROCESS_START'):\n"
        "    coverage.process_startup()\n"
    )
    try:
        if not pth.exists() or pth.read_text() != shim:
            pth.write_text(shim)
    except OSError:
        # site-packages may be read-only (e.g. system Python); silently
        # skip — local dev venvs are writable and that's where this matters.
        pass


_ensure_subprocess_coverage_shim()


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
