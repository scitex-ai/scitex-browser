"""Verify manual and pytest failure capture using an existing browser, offline."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


PAGE_FIXTURE = '''from pathlib import Path
import os
import pytest
from playwright.sync_api import sync_playwright
from scitex_browser.debugging import create_failure_capture_fixture
import scitex_browser

capture_on_failure = create_failure_capture_fixture(Path(os.environ["PROBE_ARTIFACTS"]))

@pytest.fixture
def page():
    Path("module-binding.txt").write_text(scitex_browser.__file__)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=os.environ["PROBE_EXECUTABLE"], headless=True)
        try:
            context = browser.new_context(viewport={"width": 320, "height": 200})
            context.route("**/*", lambda route: route.abort())
            page = context.new_page()
            page.set_content("<h1>Owned failure capture</h1>")
            yield page
        finally:
            browser.close()
'''

TESTS = '''def test_pass(page):
    assert page.locator("h1").inner_text() == "Owned failure capture"

def test_fail(page):
    page.evaluate("console.error('fixture-console-marker')")
    assert False, "Intentional probe call failure"
'''


def inspect_artifacts(files, marker, output, prefix):
    assert set(files) == {"screenshot", "console_logs", "page_html"}, files
    assert "Owned failure capture" in files["page_html"].read_text()
    assert marker in files["console_logs"].read_text()
    png = files["screenshot"].read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", png[16:24]) == (320, 200)
    exported = {}
    for name, path in files.items():
        target = output / (prefix + "-" + name + path.suffix)
        shutil.copyfile(path, target)
        exported[name] = {"file": target.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
    return exported


def run_pytest(root, output, executable, with_hook, hook):
    workspace = root / ("with-hook" if with_hook else "without-hook")
    workspace.mkdir()
    (workspace / "conftest.py").write_text(PAGE_FIXTURE + (hook if with_hook else ""))
    (workspace / "test_owned.py").write_text(TESTS)
    artifacts = workspace / "artifacts"
    env = dict(os.environ, PROBE_EXECUTABLE=executable, PROBE_ARTIFACTS=str(artifacts), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    name = workspace.name
    args = [sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "-o", "cache_dir=" + str(workspace / "cache"), "--confcutdir=" + str(workspace), "--junitxml=" + str(output / (name + ".xml")), "test_owned.py"]
    with (output / (name + ".log")).open("x") as log:
        child = subprocess.Popen(args, cwd=workspace, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            child.wait(timeout=45)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=3)
            raise
    tree = ET.parse(output / (name + ".xml"))
    cases = tree.findall(".//testcase")
    assert child.returncode == 1 and len(cases) == 2
    assert sum(c.find("failure") is not None for c in cases) == 1
    assert all(c.find("error") is None and c.find("skipped") is None for c in cases)
    import scitex_browser
    assert (workspace / "module-binding.txt").read_text() == scitex_browser.__file__
    paths = list(artifacts.rglob("*")) if artifacts.exists() else []
    files = [f for f in paths if f.is_file()]
    if not with_hook:
        assert files == [], files
        return {"expected_child_exit": 1, "passed": 1, "intentional_call_failures": 1, "artifacts": 0}
    selected = {}
    for key, suffix in [("screenshot", "_screenshot.png"), ("console_logs", "_console.log"), ("page_html", "_page.html")]:
        matched = [f for f in files if f.name.endswith(suffix)]
        assert len(matched) == 1 and "test_fail" in matched[0].name and "test_pass" not in matched[0].name
        selected[key] = matched[0]
    assert len(files) == 3
    return {"expected_child_exit": 1, "passed": 1, "intentional_call_failures": 1, "artifacts": inspect_artifacts(selected, "fixture-console-marker", output, "fixture")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New directory for owned artifacts and expected-failure logs")
    args = parser.parse_args()
    if not args.executable.is_file() or not os.access(args.executable, os.X_OK):
        parser.error("--executable must identify an existing browser executable")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    from playwright.sync_api import sync_playwright
    import scitex_browser
    from scitex_browser.debugging import save_failure_artifacts, setup_console_interceptor
    from scitex_browser.debugging._failure_capture import PYTEST_HOOK_CODE

    with tempfile.TemporaryDirectory(prefix="scitex-failure-capture-") as directory:
        root = Path(directory)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=str(args.executable.resolve()), headless=True)
            try:
                context = browser.new_context(viewport={"width": 320, "height": 200})
                context.route("**/*", lambda route: route.abort())
                page = context.new_page()
                page.set_content("<h1>Owned failure capture</h1>")
                setup_console_interceptor(page)
                page.evaluate("console.warn('manual-console-marker')")
                try:
                    save_failure_artifacts(page, root / "obsolete-call")
                except TypeError as error:
                    assert "artifacts_dir" in str(error)
                else:
                    raise AssertionError("The obsolete two-argument example unexpectedly succeeded")
                saved = save_failure_artifacts(page, test_name="owned::manual", artifacts_dir=root / "manual")
                report = {"browser": browser.version, "manual": inspect_artifacts(saved, "manual-console-marker", output, "manual")}
            finally:
                browser.close()
        report["without_hook"] = run_pytest(root, output, str(args.executable.resolve()), False, PYTEST_HOOK_CODE)
        report["with_hook"] = run_pytest(root, output, str(args.executable.resolve()), True, PYTEST_HOOK_CODE)
        report["module"] = scitex_browser.__file__
        report["scope"] = "Owned synchronous Page and actual pytest call-failure capture only; not setup/teardown failures, async Page, live-site/fleet/installed-skill adoption or general screenshot success. Child exit1 is the asserted intentional failure control."
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))


if __name__ == "__main__":
    main()
