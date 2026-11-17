"""Hosted readiness checks reject missing settings without executing the publisher."""
import os
from pathlib import Path
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/pypi-publish-and-github-release-on-tag.yml"
NAME = "Validate publication runtime settings"


def workflow():
    return yaml.safe_load(WORKFLOW.read_text())


@pytest.mark.parametrize("image,digest,expected", [
    ("", "1" * 64, (False, True, False)),
    ("/not-mounted/qualified image.sif", "", (False, False, True)),
    ("image.sif", "1" * 63, (False, False, True)),
    ("image.sif", "1" * 65, (False, False, True)),
    ("image.sif", "g" * 64, (False, False, True)),
    ("image.sif", "A" * 64, (False, False, True)),
    ("image.sif", "1" * 64 + "\n", (False, False, True)),
    ("image.sif", "sha256:" + "1" * 64, (False, False, True)),
    ("/not-mounted/qualified image.sif", "a1" * 32, (True, False, False)),
])
def test_publisher_settings_are_checked_before_native_jobs(tmp_path, image, digest, expected):
    # Arrange
    step = next(s for s in workflow()["jobs"]["source"]["steps"] if s.get("name") == NAME)
    env = dict(os.environ, SCITEX_CI_SIF=image, SCITEX_CI_SIF_SHA256=digest)
    # Act
    result = subprocess.run(
        ["bash", "-c", step["run"]], cwd=tmp_path, env=env,
        capture_output=True, text=True, timeout=10,
    )
    output = result.stdout + result.stderr
    # Assert
    assert (result.returncode == 0, "::error::SCITEX_CI_SIF must" in output,
            "::error::SCITEX_CI_SIF_SHA256 must" in output) == expected


def test_readiness_stays_in_read_only_source_gate_without_replacing_runtime_checks():
    # Arrange
    jobs = workflow()["jobs"]
    names = [s.get("name") for s in jobs["source"]["steps"]]
    # Act
    observed = (
        names[-1], names.index(NAME) > names.index("Revalidate protected remote source"),
        jobs["source"]["runs-on"], jobs["source"]["permissions"],
        jobs["test"]["needs"], jobs["build"]["needs"],
        jobs["publish"]["steps"][-1]["run"],
        next(s["run"] for s in jobs["release"]["steps"] if s.get("name") == "Revalidate release source and archives"),
    )
    # Assert
    assert observed == (
        NAME, True, "ubuntu-latest", {"contents": "read"},
        "source", ["source", "test"],
        "bash .github/ci/exec-in-sif.sh publish-in-sif.sh 3.12",
        "bash .github/ci/exec-in-sif.sh verify-release-in-sif.sh 3.12",
    )
