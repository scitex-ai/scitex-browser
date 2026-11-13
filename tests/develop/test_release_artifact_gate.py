"""Real immutable source builds exercise the Browser artifact gate."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/ci/release-identity.py"
COMMIT = "e0bd630395097e2646adb441749a26de13b476fa"
GIT_ENV = {
    "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
    "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
}


def test_publisher_verifies_artifacts_before_requesting_credentials():
    # Arrange
    source = (ROOT / ".github/ci/publish-in-sif.sh").read_text()
    body = source.split("set -euo pipefail", 1)[1]

    # Act
    verification = body.find("bash .github/ci/verify-release-in-sif.sh")
    request = body.index(': "${ACTIONS_ID_TOKEN_REQUEST_TOKEN')
    gate = (ROOT / ".github/ci/verify-release-in-sif.sh").read_text()

    # Assert
    assert (
        0 <= verification < request,
        0 <= gate.find("release-identity.py verify-proof") < gate.find("release-source.py"),
    ) == (True, True)


def test_release_jobs_bind_artifact_expectations_to_source_and_version():
    # Arrange
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/pypi-publish-and-github-release-on-tag.yml").read_text()
    )

    # Act
    jobs = workflow["jobs"]
    publish = next(
        row for row in jobs["publish"]["steps"]
        if row.get("run", "").endswith("publish-in-sif.sh 3.12")
    )
    observed = (
        jobs["build"]["with"]["source_commit"],
        jobs["build"]["with"]["release_tag"],
        publish["env"]["SCITEX_BROWSER_RELEASE_SOURCE_SHA"],
        publish["env"]["SCITEX_BROWSER_RELEASE_VERSION"],
    )

    # Assert
    assert observed == (
        "${{ needs.source.outputs.source_sha }}", "${{ needs.source.outputs.version }}",
        "${{ needs.source.outputs.source_sha }}", "${{ needs.source.outputs.version }}",
    )


@pytest.fixture
def archives():
    with tempfile.TemporaryDirectory(prefix="browser-artifact-gate-", dir="/tmp") as name:
        root = Path(name)
        source, output = root / "source", root / "dist"
        source.mkdir()
        coverage = root / "coverage"
        coverage.mkdir()
        environment = dict(os.environ, COVERAGE_FILE=str(coverage / ".coverage"))
        for args in (
            ["init", "--template="],
            ["remote", "add", "origin", "https://github.com/scitex-ai/scitex-browser.git"],
            ["fetch", "--depth=1", "origin", COMMIT],
            ["checkout", "--detach", COMMIT],
        ):
            subprocess.run(
                ["git", "-C", str(source), *args], env=GIT_ENV,
                check=True, capture_output=True, text=True, timeout=60,
            )
        subprocess.run(
            [sys.executable, "-m", "build", "--no-isolation", "--outdir", str(output), str(source)],
            env=environment, check=True, capture_output=True, text=True, timeout=180,
        )
        yield source, output, environment


def test_real_build_proof_accepts_source_and_refuses_modified_inputs(archives):
    # Arrange
    source, output, environment = archives
    base = [
        sys.executable, "-I", "-S", str(SCRIPT),
        "--commit", COMMIT, "--version", "0.1.15", "--dist", str(output),
    ]

    def invoke(mode, arguments=base):
        return subprocess.run(
            [*arguments, mode], cwd=source, env=environment,
            capture_output=True, text=True, timeout=120,
        )

    # Act
    # Verify real normal artifacts, then modify only owned fixture inputs.
    written = invoke("write-proof")
    verified = invoke("verify-proof")
    proof_path = output / "release-proof.json"
    original_proof = proof_path.read_bytes()
    changed = json.loads(original_proof)
    changed["source_membership"]["wheel_sha256"] = "0" * 64
    proof_path.write_text(json.dumps(changed))
    bad_proof = invoke("verify-proof")
    proof_path.write_bytes(original_proof)
    wheel, = output.glob("*.whl")
    original_wheel = wheel.read_bytes()
    wheel.write_bytes(original_wheel + b"\nchanged archive boundary\n")
    bad_wheel = invoke("verify-proof")
    wheel.write_bytes(original_wheel)
    (output / "foreign.txt").write_text("unreviewed artifact")
    extra_file = invoke("verify-proof")
    wrong_version = list(base)
    wrong_version[wrong_version.index("--version") + 1] = "0.1.16"
    bad_version = invoke("verify-proof", wrong_version)

    # Assert
    proof = json.loads(written.stdout)
    assert (
        written.returncode, verified.returncode,
        proof["commit"], proof["source_membership"]["wheel_public_members"],
        proof["source_membership"]["sdist_public_members"],
        bad_proof.returncode != 0, bad_wheel.returncode != 0,
        extra_file.returncode != 0, "Expected version and Git project metadata differ" in bad_version.stderr,
    ) == (0, 0, COMMIT, 190, 269, True, True, True, True)
