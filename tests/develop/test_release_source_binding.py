"""Exercise the release workflow's real shell guards with local Git repositories."""

import os
import subprocess
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/pypi-publish-and-github-release-on-tag.yml"


def _workflow():
    return yaml.safe_load(WORKFLOW.read_text())


def _step(job, name):
    return next(s for s in _workflow()["jobs"][job]["steps"] if s.get("name") == name)


@pytest.mark.parametrize("job", ["test", "build"])
@pytest.mark.parametrize(
    ("event", "ref", "tag", "expected"),
    [
        ("push", "refs/tags/v0.1.16", "", (True, "version=v0.1.16\n")),
        ("workflow_dispatch", "refs/heads/main", "v0.1.16", (True, "version=v0.1.16\n")),
        ("push", "refs/heads/main", "", (False, "")),
        ("workflow_dispatch", "", "", (False, "")),
        ("workflow_dispatch", "", "$(touch unexpected-file)", (False, "")),
        ("workflow_dispatch", "", "v0.1.16;exit 0", (False, "")),
        ("pull_request", "", "v0.1.16", (False, "")),
    ],
)
def test_release_tag_selection(tmp_path, job, event, ref, tag, expected):
    # Arrange
    output = tmp_path / "output"
    output.touch()
    env = dict(
        os.environ, GITHUB_EVENT_NAME=event, GITHUB_REF=ref,
        SCITEX_BROWSER_RELEASE_TAG=tag, GITHUB_OUTPUT=str(output),
    )
    script = _step(job, "Resolve version")["run"]

    # Act
    result = subprocess.run(
        ["bash", "-c", script], cwd=tmp_path, env=env,
        capture_output=True, text=True, timeout=10,
    )

    # Assert
    assert (result.returncode == 0, output.read_text(), (tmp_path / "unexpected-file").exists()) == (*expected, False)


@pytest.fixture
def release_repository(tmp_path):
    """Real main ancestry and a divergent commit; no network or global config."""
    repo = tmp_path / "repository"
    repo.mkdir()
    git = ["git", "-C", str(repo), "-c", "user.name=Release Test",
           "-c", "user.email=release-test@example.invalid"]
    subprocess.run([*git, "init", "-b", "main"], check=True, capture_output=True)
    shas = {}
    for label in ("first", "main"):
        (repo / "content").write_text(label)
        subprocess.run([*git, "add", "content"], check=True, capture_output=True)
        subprocess.run([*git, "commit", "-m", label], check=True, capture_output=True)
        shas[label] = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    subprocess.run([*git, "update-ref", "refs/remotes/origin/main", shas["main"]], check=True)
    subprocess.run([*git, "checkout", "-b", "side", shas["first"]], check=True, capture_output=True)
    (repo / "content").write_text("side")
    subprocess.run([*git, "commit", "-am", "side"], check=True, capture_output=True)
    shas["side"] = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    return repo, git, shas


@pytest.mark.parametrize("job", ["test", "build"])
@pytest.mark.parametrize(
    ("checkout", "trigger", "expected"),
    [("main", "main", "main"), ("first", "main", ""), ("side", "side", "")],
)
def test_release_source_guard(tmp_path, release_repository, job, checkout, trigger, expected):
    # Arrange
    repo, git, shas = release_repository
    subprocess.run([*git, "checkout", "--detach", shas[checkout]], check=True, capture_output=True)
    output = tmp_path / "output"
    output.touch()
    env = dict(os.environ, GITHUB_SHA=shas[trigger], GITHUB_OUTPUT=str(output))
    outcomes = {"main": (True, "sha=" + shas["main"] + "\n"), "": (False, "")}
    script = _step(job, "Verify tagged source matches the tested trigger")["run"]

    # Act
    result = subprocess.run(
        ["bash", "-c", script], cwd=repo, env=env,
        capture_output=True, text=True, timeout=10,
    )

    # Assert
    assert (result.returncode == 0, output.read_text()) == outcomes[expected]


def test_publisher_uses_recorded_build_source():
    # Arrange
    jobs = _workflow()["jobs"]
    checkout = next(s for s in jobs["publish"]["steps"] if "actions/checkout@" in s.get("uses", ""))

    # Act
    observed = (
        jobs["build"]["outputs"]["source_sha"],
        checkout["with"]["ref"],
        jobs["release"]["steps"][0]["with"]["ref"],
        jobs["publish"]["needs"],
    )

    # Assert
    assert observed == (
        "${{ steps.source.outputs.sha }}",
        "${{ needs.build.outputs.source_sha }}",
        "${{ needs.build.outputs.source_sha }}",
        "build",
    )


@pytest.mark.parametrize("job", ["test", "build"])
def test_release_input_is_passed_through_environment(job):
    # Arrange
    step = _step(job, "Resolve version")

    # Act
    observed = step["env"]

    # Assert
    assert observed == {"SCITEX_BROWSER_RELEASE_TAG": "${{ inputs.version }}"}
