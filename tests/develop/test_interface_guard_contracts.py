"""Check Browser's cross-package failure and CLA isolation contracts."""

import runpy
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]


def _import_gate():
    namespace = runpy.run_path(
        str(ROOT / "tests/integration/test_cross_package_imports.py")
    )
    return namespace["test_cross_package_import_resolves_to_real_module"]


def _gate_failure(module_name):
    """Keep pytest's BaseException-derived skip distinct from an import failure."""
    try:
        _import_gate()(module_name)
    except BaseException as error:
        return type(error)
    return None


def test_present_peer_missing_submodule_fails():
    # Arrange
    module_name = "scitex_config.scitex_gate_missing_module"

    # Act
    observed = _gate_failure(module_name)

    # Assert
    assert observed is ModuleNotFoundError


def test_absent_optional_peer_remains_a_skip():
    # Arrange
    module_name = "scitex_gate_missing_peer"

    # Act
    observed = _gate_failure(module_name)

    # Assert
    assert observed is pytest.skip.Exception


def test_cla_uses_explicit_hosted_runner_and_single_secret():
    # Arrange
    document = yaml.safe_load((ROOT / ".github/workflows/cla.yml").read_text())
    job = document["jobs"]["call"]

    # Act
    observed = (job["uses"], job["with"], job["secrets"])

    # Assert
    assert observed == (
        "scitex-ai/.github/.github/workflows/cla.yml@49ecabbd7e6876f1712f43c1f6b901aa77f4b1ae",
        {"runs_on": '["ubuntu-latest"]', "owner_allowlist": "bot*,ywatanabe1989,LLEmacs"},
        {"GH_PERSONAL_ACCESS_TOKEN": "${{ secrets.GH_PERSONAL_ACCESS_TOKEN }}"},
    )
