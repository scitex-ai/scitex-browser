"""Release callers keep hosted source resolution and pinned native build wiring."""

from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/pypi-publish-and-github-release-on-tag.yml"


def jobs():
    return yaml.safe_load(WORKFLOW.read_text())["jobs"]


def test_test_and_build_use_the_same_immutable_shared_executor_without_secrets():
    # Arrange
    workflow = jobs()
    # Act
    executors = [workflow[name]["uses"] for name in ("test", "build")]
    # Assert
    assert (
        executors[0] == executors[1],
        re.fullmatch(
            r"scitex-ai/\.github/\.github/workflows/leaf-release-sif\.yml@[0-9a-f]{40}",
            executors[0],
        ) is not None,
        all("secrets" not in workflow[name] for name in ("test", "build")),
        [workflow[name]["with"]["operation"] for name in ("test", "build")],
    ) == (True, True, True, ["test", "build"])


def test_dependency_chain_requires_full_tests_and_build_before_publication():
    # Arrange
    workflow = jobs()
    # Act
    observed = [workflow[name]["needs"] for name in ("test", "build", "publish", "release")]
    # Assert
    assert observed == [
        "source", ["source", "test"], ["source", "build"], ["source", "build", "publish"],
    ]


def test_both_publication_jobs_download_only_the_recorded_sources_artifact():
    # Arrange
    workflow = jobs()
    # Act
    names = [
        next(step for step in workflow[name]["steps"] if step.get("uses") == "actions/download-artifact@v4")["with"]["name"]
        for name in ("publish", "release")
    ]
    # Assert
    assert names == ["browser-dist-${{ needs.source.outputs.source_sha }}"] * 2


def test_remote_preflight_runs_hosted_with_read_only_permissions_and_pinned_python():
    # Arrange
    source = jobs()["source"]
    # Act
    setup = next(step for step in source["steps"] if step.get("uses", "").startswith("actions/setup-python@"))
    remote = next(step for step in source["steps"] if step.get("name") == "Revalidate protected remote source")
    # Assert
    assert (
        source["runs-on"], source["permissions"], setup, remote["env"], remote["run"],
    ) == (
        "ubuntu-latest", {"contents": "read"},
        {"uses": "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065", "with": {"python-version": "3.12"}},
        {
            "GITHUB_TOKEN": "${{ github.token }}",
            "SCITEX_BROWSER_RELEASE_SOURCE_SHA": "${{ steps.source.outputs.sha }}",
            "SCITEX_BROWSER_RELEASE_VERSION": "${{ steps.ver.outputs.version }}",
        },
        'python -I -S -B .github/ci/release-source.py --tag "$SCITEX_BROWSER_RELEASE_VERSION" --commit "$SCITEX_BROWSER_RELEASE_SOURCE_SHA"',
    )
