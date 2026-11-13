"""Source revalidation rejects malformed requests and preserves both boundaries."""

from pathlib import Path
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/ci/release-source.py"


@pytest.mark.parametrize(
    ("tag", "commit", "message"),
    [
        ("v0.1.15;touch unexpected-file", "a" * 40, "existing vX.Y.Z tag"),
        ("v0.1.15/other", "a" * 40, "existing vX.Y.Z tag"),
        ("v01.1.15", "a" * 40, "existing vX.Y.Z tag"),
        ("v0.1.15", "main", "immutable commit"),
        ("v0.1.15", "A" * 40, "immutable commit"),
    ],
)
def test_malformed_source_request_refuses_before_remote_lookup(tmp_path, tag, commit, message):
    # Arrange
    command = [
        sys.executable, "-I", "-S", str(SCRIPT),
        "--tag", tag, "--commit", commit,
    ]

    # Act
    result = subprocess.run(
        command, cwd=tmp_path, capture_output=True, text=True, timeout=10,
    )

    # Assert
    assert (
        result.returncode != 0, message in result.stderr,
        (tmp_path / "unexpected-file").exists(),
    ) == (True, True, False)


def test_github_release_revalidates_same_build_before_creating_assets():
    # Arrange
    jobs = yaml.safe_load(
        (ROOT / ".github/workflows/pypi-publish-and-github-release-on-tag.yml").read_text()
    )["jobs"]
    steps = jobs["release"]["steps"]
    gate = next(s for s in steps if s.get("name") == "Revalidate release source and archives")
    publish = next(
        s for s in jobs["publish"]["steps"]
        if s.get("run", "").endswith("publish-in-sif.sh 3.12")
    )

    # Act
    observed = (
        gate["run"], gate["env"],
        steps.index(gate) < next(i for i, s in enumerate(steps) if s.get("name") == "Create GitHub Release"),
        publish["env"]["GITHUB_TOKEN"],
        jobs["publish"]["permissions"], jobs["release"]["permissions"],
    )

    # Assert
    assert observed == (
        "bash .github/ci/exec-in-sif.sh verify-release-in-sif.sh 3.12",
        {
            "SCITEX_BROWSER_RELEASE_SOURCE_SHA": "${{ needs.build.outputs.source_sha }}",
            "SCITEX_BROWSER_RELEASE_VERSION": "${{ needs.build.outputs.version }}",
            "GITHUB_TOKEN": "${{ github.token }}",
        },
        True, "${{ github.token }}",
        {"contents": "read", "id-token": "write"}, {"contents": "write"},
    )
