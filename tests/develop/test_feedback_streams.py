"""Public feedback stays on its intended stream under a warning root level."""

import json
import os
import subprocess
import sys
import textwrap

import pytest


CACHE = (
    "import asyncio\n"
    "from scitex_browser.collaboration.credential_manager import CredentialManager\n"
    "manager = CredentialManager(verbose={verbose})\n"
    "manager.cache['sample'] = 'fixture-value'\n"
    "returned = asyncio.run(manager.get_credential('sample'))\n"
)
AUTH = (
    "from scitex_browser.auth.google import GoogleAuthHelper\n"
    "helper = GoogleAuthHelper(email='probe@example.invalid', password='fixture-value', debug={debug})\n"
    "helper._log('auth-probe')\n"
)


@pytest.mark.parametrize(
    ("code", "needle", "expected"),
    [
        (
            "import scitex_browser.collaboration",
            "unused-probe",
            {"stdout": False, "stderr": False, "message": False, "returned": None},
        ),
        (
            CACHE.format(verbose=False),
            "Using cached sample",
            {"stdout": False, "stderr": False, "message": False, "returned": "fixture-value"},
        ),
        (
            CACHE.format(verbose=True),
            "Using cached sample",
            {"stdout": True, "stderr": False, "message": True, "returned": "fixture-value"},
        ),
        (
            AUTH.format(debug=False),
            "auth-probe",
            {"stdout": False, "stderr": False, "message": False, "returned": None},
        ),
        (
            AUTH.format(debug=True),
            "auth-probe",
            {"stdout": False, "stderr": True, "message": True, "returned": None},
        ),
    ],
    ids=["quiet-import", "quiet-cache", "visible-cache", "quiet-auth", "visible-auth"],
)
def test_feedback_keeps_stream_and_flag_contract(tmp_path, code, needle, expected):
    # Arrange
    environment = dict(os.environ, SCITEX_LOGGING_LEVEL="WARNING")
    environment.pop("GOOGLE_AUTH_DEBUG", None)
    script = (
        "import contextlib, io, json\n"
        "out, err = io.StringIO(), io.StringIO()\n"
        "returned = None\n"
        "with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):\n"
        + textwrap.indent(code, "    ")
        + "\n"
        + "print(json.dumps({'stdout': bool(out.getvalue()), 'stderr': bool(err.getvalue()), "
        + "'message': "
        + repr(needle)
        + " in out.getvalue() + err.getvalue(), 'returned': returned}))\n"
    )

    # Act
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path, env=environment, capture_output=True, text=True,
        timeout=15, check=True,
    )
    observed = json.loads(result.stdout)

    # Assert
    assert observed == expected
