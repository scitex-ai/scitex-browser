---
description: |
  [TOPIC] Session Lifecycle
  [DETAILS] Session Lifecycle — see file body for details.
tags: [scitex-browser-session-lifecycle]
---

# Session Lifecycle

Two flavors ship: the synchronous zombie-safe session (small tests,
scripts) and the shared collaborative session (multi-agent).

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

## TestMonitor

Takes periodic screenshots of a running browser test (default 1 Hz).

```python
from scitex_browser import monitor_test

async with monitor_test(page, out_dir="screens/") as m:
    ...   # your test body
```
