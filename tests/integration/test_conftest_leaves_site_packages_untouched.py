"""Regression test: importing conftest must not touch site-packages or env."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

CONFTEST_PATH = Path(__file__).resolve().parents[1] / "conftest.py"


def test_conftest_leaves_site_packages_untouched():
    # Arrange
    child_code = textwrap.dedent(
        f"""\
        import os
        import runpy
        import site

        os.environ["COVERAGE_PROCESS_START"] = "SENTINEL_PROCESS_START"
        os.environ["COVERAGE_FILE"] = "SENTINEL_COVERAGE_FILE"

        dirs = []
        try:
            dirs.extend(site.getsitepackages())
        except Exception:
            pass
        try:
            user_site = site.getusersitepackages()
        except Exception:
            user_site = None
        if user_site:
            dirs.append(user_site)

        before = {{}}
        for d in dirs:
            try:
                before[d] = set(os.listdir(d))
            except OSError:
                before[d] = None

        runpy.run_path({str(CONFTEST_PATH)!r}, run_name="conftest_check")

        after = {{}}
        for d in dirs:
            try:
                after[d] = set(os.listdir(d))
            except OSError:
                after[d] = None

        assert before == after, "conftest.py created files in site-packages"
        assert os.environ["COVERAGE_PROCESS_START"] == "SENTINEL_PROCESS_START"
        assert os.environ["COVERAGE_FILE"] == "SENTINEL_COVERAGE_FILE"
        """
    )
    # Act
    proc = subprocess.run(
        [sys.executable, "-c", child_code],
        capture_output=True,
        text=True,
    )
    # Assert
    assert proc.returncode == 0, proc.stderr
