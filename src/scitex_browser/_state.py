#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local-state path helpers for scitex-browser.

Every disk write owned by this package goes through one of the helpers
here, so the on-disk layout is always:

    $SCITEX_DIR/browser/runtime/<category>/...

Public helper names mirror the historical logical categories
(``screenshots``, ``sessions``, ``persistent``, ``memory``,
``cache``, ``test_monitor``, ``capture``); only the on-disk layout
moved under ``runtime/``. Callers that need to honour a user-supplied
override (e.g. ``screenshot_dir=`` kwarg) pass it through ``direct_val``;
when ``None``, the canonical runtime path is returned.

See the local-state-directories skill (general/01_ecosystem_06) for the
canonical layout rules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from scitex_config._ecosystem import local_state

__all__ = [
    "runtime_dir",
    "cache_dir",
    "capture_dir",
    "memory_dir",
    "persistent_dir",
    "screenshots_dir",
    "sessions_dir",
    "test_monitor_dir",
]

PathLike = Union[str, Path]


def _resolve_override(direct_val: Optional[PathLike]) -> Optional[Path]:
    """Return ``Path(direct_val).expanduser()`` or ``None``.

    Mirrors ``ScitexPaths.resolve``'s direct-value precedence: when a
    caller explicitly hands in a path, we use it verbatim (after
    ``~``-expansion) and never substitute the runtime default.
    """
    if direct_val is None:
        return None
    return Path(direct_val).expanduser()


def runtime_dir(*parts: str) -> Path:
    """Resolve any sub-path under ``$SCITEX_DIR/browser/runtime/``.

    The runtime root + its canonical ``.gitkeep``/``README.md`` seeds
    are created lazily by ``local_state.runtime_path`` on first call.
    """
    return local_state.runtime_path("browser", *parts)


def cache_dir(direct_val: Optional[PathLike] = None) -> Path:
    """Browser cache root — ``runtime/cache/`` by default."""
    override = _resolve_override(direct_val)
    return override if override is not None else runtime_dir("cache")


def capture_dir(direct_val: Optional[PathLike] = None) -> Path:
    """Live-page capture directory — ``runtime/capture/`` by default.

    Distinct from ``screenshots_dir`` (the BrowserLogger timeline) and
    ``test_monitor_dir`` (periodic-screenshot worker).
    """
    override = _resolve_override(direct_val)
    return override if override is not None else runtime_dir("capture")


def memory_dir(direct_val: Optional[PathLike] = None) -> Path:
    """Persistent-memory JSON files — ``runtime/memory/`` by default."""
    override = _resolve_override(direct_val)
    return override if override is not None else runtime_dir("memory")


def persistent_dir(direct_val: Optional[PathLike] = None) -> Path:
    """Persistent-browser user-data dir — ``runtime/persistent/`` by default."""
    override = _resolve_override(direct_val)
    return override if override is not None else runtime_dir("persistent")


def screenshots_dir(direct_val: Optional[PathLike] = None) -> Path:
    """BrowserLogger screenshot timeline — ``runtime/screenshots/`` by default."""
    override = _resolve_override(direct_val)
    return override if override is not None else runtime_dir("screenshots")


def sessions_dir(
    session_id: Optional[str] = None,
    direct_val: Optional[PathLike] = None,
) -> Path:
    """Shared-session user-data dirs — ``runtime/sessions/[<id>/]`` by default.

    Pass ``session_id`` to get the per-session subdirectory; omit it for
    the parent ``sessions/`` root. A non-``None`` ``direct_val`` wins and
    is returned verbatim.
    """
    override = _resolve_override(direct_val)
    if override is not None:
        return override
    if session_id:
        return runtime_dir("sessions", session_id)
    return runtime_dir("sessions")


def test_monitor_dir(direct_val: Optional[PathLike] = None) -> Path:
    """Test-monitor periodic-screenshot dir — ``runtime/test_monitor/`` by default."""
    override = _resolve_override(direct_val)
    return override if override is not None else runtime_dir("test_monitor")


# EOF
