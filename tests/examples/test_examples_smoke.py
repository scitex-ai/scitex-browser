"""Smoke tests: every example script must run to completion."""

import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES = sorted(Path(__file__).parent.parent.joinpath("examples").glob("*.py"))


def test_examples_directory_is_not_empty():
    # Arrange
    discovered = EXAMPLES
    # Act
    count = len(discovered)
    # Assert
    assert count > 0, "no example scripts found"


@pytest.mark.parametrize("example_path", EXAMPLES, ids=lambda p: p.name)
def test_example_script_runs_with_exit_code_zero(example_path, tmp_path):
    # Arrange
    cmd = [sys.executable, str(example_path)]
    # Act
    result = subprocess.run(
        cmd,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
    )
    # Assert
    assert result.returncode == 0, f"{example_path.name} failed: {result.stderr}"
