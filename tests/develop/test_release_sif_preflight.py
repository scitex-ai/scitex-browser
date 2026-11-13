"""Real preflight refusals; these cases never execute a SIF or publisher."""

import hashlib
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / ".github/ci/exec-in-sif.sh"


@pytest.fixture
def refusal_environment(tmp_path):
    image = tmp_path / "invalid image.sif"
    image.write_bytes(b"Deliberately not a container: preflight refusal fixture.")
    jobs = tmp_path / "job space"
    jobs.mkdir()
    return dict(
        os.environ,
        SCITEX_CI_APPTAINER=sys.executable,
        SCITEX_CI_SIF=str(image),
        SCITEX_CI_SIF_SHA256=hashlib.sha256(image.read_bytes()).hexdigest(),
        RUNNER_TEMP=str(jobs),
    )


def _invoke(environment):
    return subprocess.run(
        ["/bin/bash", str(WRAPPER), "build-in-sif.sh", "3.12"],
        cwd=ROOT, env=environment, capture_output=True, text=True, timeout=15,
    )


def test_missing_digest_is_refused_before_image_access(tmp_path, refusal_environment):
    # Arrange
    environment = refusal_environment
    environment.pop("SCITEX_CI_SIF_SHA256")
    environment["SCITEX_CI_SIF"] = str(tmp_path / "absent.sif")

    # Act
    result = _invoke(environment)

    # Assert
    assert (result.returncode != 0, "SCITEX_CI_SIF_SHA256" in result.stdout + result.stderr) == (True, True)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"SCITEX_CI_SIF_SHA256": "0" * 64}, "digest mismatch"),
        ({"RUNNER_TEMP": ""}, "RUNNER_TEMP"),
        ({"RUNNER_TEMP": "relative-job-space"}, "absolute directory"),
        ({"RUNNER_TEMP": "{root}/bad:bind"}, "unsupported bind separator"),
    ],
    ids=["wrong-digest", "missing-scratch", "relative-scratch", "separator-scratch"],
)
def test_invalid_release_preflight_is_refused(tmp_path, refusal_environment, changes, message):
    # Arrange
    environment = refusal_environment
    environment.update({key: value.format(root=tmp_path) for key, value in changes.items()})

    # Act
    result = _invoke(environment)

    # Assert
    assert (result.returncode != 0, message in result.stdout + result.stderr) == (True, True)


def test_release_workflow_supplies_required_image_digest():
    # Arrange
    path = ROOT / ".github/workflows/pypi-publish-and-github-release-on-tag.yml"
    workflow = yaml.safe_load(path.read_text())

    # Act
    supplied = workflow["env"].get("SCITEX_CI_SIF_SHA256")

    # Assert
    assert supplied == "${{ vars.SCITEX_CI_SIF_SHA256 }}"
