"""The declared development auditor is mandatory, including module-only installs."""

from pathlib import Path

from scitex_dev.testing import audit_all_for_package


def test_audit_all_clean():
    # Arrange
    package_root = Path(__file__).resolve().parents[2]

    # Act
    # The shared helper raises on failed or unavailable audit execution.
    result = audit_all_for_package("scitex-browser", path=package_root)

    # Assert
    assert result is None
