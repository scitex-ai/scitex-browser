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

# EOF
