"""Offline tests for the dedicated-profile launcher (no Chrome is started)."""

import pytest

from scitex_browser.flows import _dedicated_profile as dp


def _alive(_port, timeout=2.0):
    return {"Browser": "Chrome/test"}


def _dead(_port, timeout=2.0):
    return None


def _write_port(path, port):
    (path / "DevToolsActivePort").write_text(f"{port}\n/devtools/browser/x\n")


@pytest.mark.parametrize(
    "path",
    [
        r"C:\Users\u\AppData\Local\Google\Chrome\User Data",
        "/home/u/.config/google-chrome",
        "/Users/u/Library/Application Support/Google/Chrome/",
    ],
)
def test_default_profiles_are_refused(path):
    # Arrange
    profile = path
    # Act
    call = lambda: dp.launch_dedicated_chrome(profile)  # noqa: E731
    # Assert
    with pytest.raises(dp.DedicatedProfileError):
        call()


@pytest.mark.parametrize(
    "flag",
    [
        "--remote-debugging-address=127.0.0.1",
        "--remote-debugging-port=0",
        "--headless=new",
        "--user-data-dir=/p",
    ],
)
def test_launch_argv_contains_safety_flag(flag):
    # Arrange
    args = ("chrome", "/p", True, 0, (800, 600))
    # Act
    argv = dp._launch_argv(*args)
    # Assert
    assert flag in argv


def test_launch_argv_headed_has_no_headless_flag():
    # Arrange
    args = ("chrome", "/p", False, 9222, (800, 600))
    # Act
    argv = dp._launch_argv(*args)
    # Assert
    assert not any(a.startswith("--headless") for a in argv)


def test_read_devtools_active_port_reads_port(tmp_path):
    # Arrange
    _write_port(tmp_path, 50965)
    # Act
    port, _ws, _mtime = dp.read_devtools_active_port(tmp_path)
    # Assert
    assert port == 50965


def test_malformed_devtools_file_raises(tmp_path):
    # Arrange
    (tmp_path / "DevToolsActivePort").write_text("garbage\n")
    # Act
    call = lambda: dp.read_devtools_active_port(tmp_path)  # noqa: E731
    # Assert
    with pytest.raises(dp.DedicatedProfileError):
        call()


def test_attach_ignores_stale_port_file(tmp_path):
    # Arrange
    _write_port(tmp_path, 1)
    # Act
    chrome = dp.attach_dedicated_chrome(str(tmp_path), probe=_dead)
    # Assert
    assert chrome is None


def test_attach_reports_loopback_cdp_url(tmp_path):
    # Arrange
    _write_port(tmp_path, 4242)
    # Act
    chrome = dp.attach_dedicated_chrome(str(tmp_path), probe=_alive)
    # Assert
    assert chrome.cdp_url == "http://127.0.0.1:4242"


def test_close_never_touches_an_attached_instance(tmp_path):
    # Arrange
    _write_port(tmp_path, 4242)
    chrome = dp.attach_dedicated_chrome(str(tmp_path), probe=_alive)
    # Act
    closed = chrome.close()
    # Assert
    assert closed is False


def test_missing_profile_dir_raises(tmp_path):
    # Arrange
    missing = str(tmp_path / "nope")
    # Act
    call = lambda: dp.launch_dedicated_chrome(  # noqa: E731
        missing, chrome_path="/bin/chrome", reuse=False, timeout=0.1, probe=_dead
    )
    # Assert
    with pytest.raises(dp.DedicatedProfileError):
        call()


def test_launch_marks_instance_as_launched_after_fresh_port_file(tmp_path):
    # Arrange
    def start(_argv):
        _write_port(tmp_path, 5555)

    # Act
    chrome = dp.launch_dedicated_chrome(
        str(tmp_path),
        chrome_path="/bin/chrome",
        reuse=False,
        timeout=5,
        probe=_alive,
        start_process=start,
    )
    # Assert
    assert (chrome.launched, chrome.port) == (True, 5555)


def test_launch_times_out_when_no_listener_appears(tmp_path):
    # Arrange
    def start(_argv):
        return None  # e.g. profile already open in an ordinary window

    # Act
    call = lambda: dp.launch_dedicated_chrome(  # noqa: E731
        str(tmp_path),
        chrome_path="/bin/chrome",
        reuse=False,
        timeout=0.5,
        probe=_alive,
        start_process=start,
    )
    # Assert
    with pytest.raises(dp.DedicatedProfileError):
        call()
