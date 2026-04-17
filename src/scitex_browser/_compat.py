#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compatibility shims for optional scitex dependencies."""

from __future__ import annotations

import os
from pathlib import Path


def _get_default_dir() -> Path:
    """Return default output directory for browser artifacts."""
    base = os.environ.get("SCITEX_DIR", str(Path.home() / ".scitex"))
    return Path(base)


class _PathResolver:
    """Minimal path resolver matching scitex.config.get_paths() API."""

    def resolve(self, *parts: str) -> Path:
        return _get_default_dir().joinpath(*parts)


def get_paths() -> _PathResolver:
    """Return scitex path resolver, falling back to local impl."""
    try:
        from scitex.config import get_paths as _get_paths

        return _get_paths()
    except ImportError:
        return _PathResolver()


class ScholarError(Exception):
    """Standalone ScholarError for when scitex is not installed."""

    pass


try:
    from scitex.logging import ScholarError as _SE

    ScholarError = _SE  # type: ignore[misc]
except ImportError:
    pass


class _StandaloneScholarConfig:
    """Minimal ScholarConfig replacement used when scitex.scholar is unavailable."""

    def get_cache_chrome_dir(self, profile_name: str) -> Path:
        return _get_default_dir() / "cache" / "chrome" / profile_name


def get_scholar_config():
    """Return a ScholarConfig if scitex.scholar is importable, else a local fallback."""
    try:
        from scitex.scholar.config import ScholarConfig

        return ScholarConfig()
    except ImportError:
        return _StandaloneScholarConfig()


# EOF
