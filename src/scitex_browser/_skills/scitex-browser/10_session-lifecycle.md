---
description: |
  [TOPIC] Session Lifecycle
  [DETAILS] Session Lifecycle — see file body for details.
tags: [scitex-browser-session-lifecycle]
---

# Session Lifecycle

Use a fresh session for public pages and isolated tests. Attach to a
dedicated browser profile when a task needs an existing sign-in.

## SyncBrowserSession (sync API)

```python
from scitex_browser import SyncBrowserSession

with SyncBrowserSession(headless=False) as s:
    s.page.goto("https://example.org")
    # s.browser, s.context, s.page all available
```

Key property: on `__exit__` it terminates any leaked Chromium processes
whose parent is this Python PID — prevents "zombie" browsers when a
test errors out.

## pytest fixture

```python
from scitex_browser import create_browser_session_fixture

browser_session = create_browser_session_fixture(headless=True)
# use as a regular pytest fixture returning SyncBrowserSession
```

## SharedBrowserSession (collaboration, experimental)

```python
from scitex_browser.collaboration import SharedBrowserSession, SessionConfig

cfg = SessionConfig(profile_dir="/tmp/shared-profile")
async with SharedBrowserSession(cfg) as session:
    ...
```

Designed for long-lived sessions shared across multiple agents/humans;
persists cookies/profile between runs. Module is marked
`__experimental__ = True`.

## Authenticated Windows Chrome from WSL

1. Reserve a separate Windows Chrome user data directory for the task. Launch
   Chrome with only that profile and the target URL. Let the user complete
   sign-in and MFA in the regular window, then close that window normally so
   Chrome saves the session. Use the same directory for subsequent launches.
2. Start the dedicated profile headlessly. Use a loopback DevTools listener,
   an ephemeral port, and an explicit viewport. The browser keeps its own
   cookies and cache in that profile.

For example, from PowerShell on Windows (or via `powershell.exe` from WSL)
after the dedicated window has closed:

```powershell
$chrome = Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'
$profile = Join-Path $env:LOCALAPPDATA 'scitex-browser\my-task'
Start-Process -FilePath $chrome -ArgumentList @(
    "--user-data-dir=`"$profile`"",
    '--headless',
    '--remote-debugging-address=127.0.0.1',
    '--remote-debugging-port=0',
    '--window-size=1280,900',
    'about:blank'
) -WindowStyle Hidden
```

Read the first line of the profile's `DevToolsActivePort` file after launch.
In WSL mirrored networking (`wslinfo --networking-mode`), verify the current
listener at `http://127.0.0.1:<port>/json/version`. If WSL cannot reach the
loopback endpoint, run the browser client on Windows. Keep DevTools local.

```python
from scitex_browser import get_text_async

text = await get_text_async(
    authorized_url,
    cdp_url=devtools_url,
    wait_until="domcontentloaded",
)
```

The capture API navigates the first tab of the attached profile. Reserve that
tab for automation. When reading editable settings, the live value is in the
input control. With a Playwright page, use the field locator's
`input_value()` for that value. Scope captures to the requested content and
check the account or resource before reading it.

Google sign-in can reject a debugging-enabled window with a browser security
message. Return to an ordinary launch of the dedicated profile and let the
user finish authentication there. If a headless request redirects to
sign-in, treat it as an expired or missing session. Disconnecting capture
leaves Chrome running. When the task is done, close only the dedicated
instance to keep its profile available for the next task.

## TestMonitor

Takes periodic screenshots of a running browser test (default 2 s interval).

```python
from scitex_browser import TestMonitor

monitor = TestMonitor(interval=2.0)
monitor.start("my_feature_test")
try:
    ...   # your test body
finally:
    monitor.stop()
```

A decorator form is also available via `monitor_test`:

```python
from scitex_browser import monitor_test

@monitor_test(interval=1.0, auto_gif=True)
def test_my_feature(page):
    ...
```
