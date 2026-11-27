#!/usr/bin/env python3
"""Launch or attach a dedicated Chrome profile with DevTools on loopback.

A *dedicated* profile is a Chrome user-data directory reserved for automation.
The account owner signs it in once, in an ordinary window; automation then
restarts it headless with a loopback DevTools listener and drives it.

Safety rules enforced here:

- The default Chrome ``User Data`` directory is refused. Chrome refuses remote
  debugging on it anyway, and it is the user's personal profile.
- DevTools listens on ``127.0.0.1`` only.
- Profiles and cookies are never copied; the browser uses the directory in place.
- ``attached_page`` opens its own tab and closes only that tab ("tab-safe").
- ``DedicatedChrome.close`` closes only an instance this module launched.

Works natively and from WSL driving Windows Chrome (``chrome.exe`` is started
through ``powershell.exe Start-Process`` so it outlives the WSL process, and the
``DevToolsActivePort`` file is read through ``wslpath``). WSL must use mirrored
networking for the Windows loopback listener to be reachable.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator, Callable, Optional

__all__ = [
    "DedicatedProfileError",
    "DedicatedChrome",
    "launch_dedicated_chrome",
    "attach_dedicated_chrome",
    "attached_page",
    "is_wsl",
]

WINDOWS_CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
POWERSHELL = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"


class DedicatedProfileError(RuntimeError):
    """The dedicated profile could not be launched or attached safely."""


def is_wsl() -> bool:
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except OSError:
        return False


def _is_windows_path(path: str) -> bool:
    return len(path) > 2 and path[1] == ":" and path[2] in "\\/"


def _refuse_default_profile(user_data_dir: str) -> None:
    norm = user_data_dir.replace("\\", "/").rstrip("/").lower()
    defaults = (
        "google/chrome/user data",
        ".config/google-chrome",
        "library/application support/google/chrome",
        ".config/chromium",
    )
    if any(norm.endswith(d) for d in defaults):
        raise DedicatedProfileError(
            "refusing the default Chrome profile directory; use a dedicated "
            "user-data-dir reserved for automation"
        )


def _local_path(user_data_dir: str, to_local: Optional[Callable[[str], str]]) -> Path:
    """Path this process can read for a (possibly Windows) profile directory."""
    if to_local is not None:
        return Path(to_local(user_data_dir))
    if _is_windows_path(user_data_dir) and is_wsl():
        out = subprocess.run(
            ["wslpath", "-u", user_data_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        return Path(out.stdout.strip())
    return Path(user_data_dir)


def read_devtools_active_port(profile_dir: Path) -> tuple[int, str, float]:
    """Return (port, browser websocket path, mtime) from DevToolsActivePort."""
    f = profile_dir / "DevToolsActivePort"
    lines = f.read_text().splitlines()
    if len(lines) < 2 or not lines[0].strip().isdigit():
        raise DedicatedProfileError(f"malformed {f}")
    return int(lines[0]), lines[1].strip(), f.stat().st_mtime


def _probe(port: int, timeout: float = 2.0) -> Optional[dict]:
    """GET /json/version on loopback; None if nothing answers."""
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/json/version", timeout=timeout
        ) as resp:
            return json.loads(resp.read().decode())
    except (OSError, ValueError):
        return None


@dataclass
class DedicatedChrome:
    """A dedicated Chrome instance reachable over loopback DevTools."""

    user_data_dir: str
    port: int
    launched: bool
    version: dict = field(default_factory=dict)

    @property
    def cdp_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def close(self, timeout: float = 10.0) -> bool:
        """Close the instance if this module launched it. Returns True if closed.

        Uses CDP ``Browser.close`` on this instance's own endpoint, so no other
        Chrome process (e.g. the user's personal browser) is touched.
        """
        if not self.launched:
            return False
        ws_url = (self.version or _probe(self.port) or {}).get("webSocketDebuggerUrl")
        if not ws_url:
            return True  # already gone
        _cdp_browser_close(ws_url)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if _probe(self.port, timeout=1.0) is None:
                return True
            time.sleep(0.3)
        raise DedicatedProfileError(f"instance on port {self.port} did not close")


def _cdp_browser_close(ws_url: str) -> None:
    """Send Browser.close over the browser websocket via Playwright."""
    import asyncio

    from playwright.async_api import async_playwright

    async def _run() -> None:
        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(ws_url)
            session = await browser.new_browser_cdp_session()
            with contextlib.suppress(Exception):  # the socket drops on close
                await session.send("Browser.close")

    asyncio.run(_run())


def attach_dedicated_chrome(
    user_data_dir: str,
    *,
    to_local: Optional[Callable[[str], str]] = None,
    probe: Optional[Callable[[int], Optional[dict]]] = None,
) -> Optional[DedicatedChrome]:
    """Attach to an already-running debuggable instance of this profile, if any.

    ``probe(port)`` returns the ``/json/version`` dict or None; injectable for tests.
    """
    _refuse_default_profile(user_data_dir)
    probe = probe or _probe
    local = _local_path(user_data_dir, to_local)
    try:
        port, _, _ = read_devtools_active_port(local)
    except (OSError, DedicatedProfileError):
        return None
    version = probe(port)
    if version is None:
        return None  # stale file from an earlier run
    return DedicatedChrome(user_data_dir, port, launched=False, version=version)


def _launch_argv(
    chrome_path: str,
    user_data_dir: str,
    headless: bool,
    port: int,
    window_size: tuple[int, int],
) -> list[str]:
    args = [
        f"--user-data-dir={user_data_dir}",
        "--remote-debugging-address=127.0.0.1",
        f"--remote-debugging-port={port}",
        f"--window-size={window_size[0]},{window_size[1]}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    if headless:
        args.insert(1, "--headless=new")
    return [chrome_path, *args, "about:blank"]


def _start_process(argv: list[str]) -> None:
    exe, *args = argv
    if _is_windows_path(exe) and is_wsl():
        # Start-Process detaches chrome.exe from this WSL process.
        quoted = ",".join("'" + a.replace("'", "''") + "'" for a in args)
        ps = (
            f"Start-Process -FilePath '{exe}' -ArgumentList @({quoted}) "
            "-WindowStyle Hidden"
        )
        subprocess.run(
            [POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", ps],
            check=True,
            capture_output=True,
            timeout=30,
        )
    else:
        subprocess.Popen(  # noqa: S603 - argv is built here, not from a shell
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )


def launch_dedicated_chrome(
    user_data_dir: str,
    *,
    chrome_path: Optional[str] = None,
    headless: bool = True,
    port: int = 0,
    window_size: tuple[int, int] = (1280, 900),
    timeout: float = 30.0,
    to_local: Optional[Callable[[str], str]] = None,
    reuse: bool = True,
    probe: Optional[Callable[[int], Optional[dict]]] = None,
    start_process: Optional[Callable[[list], None]] = None,
) -> DedicatedChrome:
    """Launch (or, with ``reuse``, attach to) the dedicated profile.

    ``port=0`` lets Chrome pick a free port, read back from DevToolsActivePort.
    Raises DedicatedProfileError if the profile is already open without
    DevTools (Chrome would hand the launch to that window and exit), or if no
    fresh loopback listener appears within ``timeout`` seconds.
    """
    _refuse_default_profile(user_data_dir)
    probe = probe or _probe
    start_process = start_process or _start_process
    if reuse:
        running = attach_dedicated_chrome(user_data_dir, to_local=to_local, probe=probe)
        if running is not None:
            return running

    if chrome_path is None:
        chrome_path = (
            WINDOWS_CHROME
            if is_wsl() and _is_windows_path(user_data_dir)
            else (shutil.which("google-chrome") or shutil.which("chromium") or "")
        )
    if not chrome_path:
        raise DedicatedProfileError("no Chrome executable found")

    local = _local_path(user_data_dir, to_local)
    if not local.is_dir():
        raise DedicatedProfileError(f"profile directory does not exist: {local}")
    try:
        before = (local / "DevToolsActivePort").stat().st_mtime
    except OSError:
        before = 0.0

    start_process(
        _launch_argv(chrome_path, user_data_dir, headless, port, window_size)
    )

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            got_port, _, mtime = read_devtools_active_port(local)
        except (OSError, DedicatedProfileError):
            got_port, mtime = 0, 0.0
        if got_port and mtime > before:
            version = probe(got_port)
            if version is not None:
                return DedicatedChrome(user_data_dir, got_port, True, version)
        time.sleep(0.5)
    raise DedicatedProfileError(
        "no fresh DevTools listener appeared; the profile may already be open "
        "in an ordinary window (close it first) or loopback is unreachable"
    )


@contextlib.asynccontextmanager
async def attached_page(cdp_url: str) -> AsyncIterator["object"]:
    """Yield a NEW tab in the attached browser; close only that tab on exit."""
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(cdp_url)
        if not browser.contexts:
            raise DedicatedProfileError(f"browser at {cdp_url} has no context")
        page = await browser.contexts[0].new_page()
        try:
            yield page
        finally:
            with contextlib.suppress(Exception):
                await page.close()
