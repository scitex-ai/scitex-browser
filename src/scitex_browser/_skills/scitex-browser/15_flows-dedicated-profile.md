---
description: |
  [TOPIC] Reusable flows on a dedicated signed-in profile
  [DETAILS] Launch or attach a dedicated Chrome profile with loopback DevTools (WSL to Windows included), open a private tab, and create GitHub fine-grained tokens with the value handed only to a callback.
tags: [scitex-browser-flows]
---

# Flows on a dedicated profile

`scitex_browser.flows` holds reusable, human-in-the-loop-safe flows. They run
in a **dedicated** Chrome profile that the account owner signed in once, in an
ordinary window (see [Session Lifecycle](10_session-lifecycle.md)).

Rules the flows enforce:

- The default Chrome `User Data` directory is refused.
- DevTools listens on `127.0.0.1` only.
- Profiles and cookies are never copied.
- Each flow opens its **own tab** and closes only that tab.
- `DedicatedChrome.close()` closes only an instance the helper launched.
- No password is typed and no 2FA is answered. A sign-in, sudo
  ("Confirm access") or 2FA page raises `GitHubAuthPromptError`.

## Launch or attach

```python
from scitex_browser.flows import launch_dedicated_chrome, attached_page

chrome = launch_dedicated_chrome(
    r"C:\Users\me\AppData\Local\scitex-browser\automation-profile"
)  # headless, --remote-debugging-port=0, reads DevToolsActivePort
async with attached_page(chrome.cdp_url) as page:
    ...
chrome.close()
```

From WSL, a Windows path starts `chrome.exe` through `powershell.exe
Start-Process`. WSL must use mirrored networking (`wslinfo --networking-mode`)
to reach the Windows loopback listener. If the profile is already open in an
ordinary window, the launch fails with `DedicatedProfileError`. Close that
window first.

## GitHub fine-grained token

```python
from scitex_browser.flows import github_create_fine_grained_token

facts = github_create_fine_grained_token(
    "fleet-agents-myorg",
    "myorg",                       # resource owner
    repos="all",                   # or "public"; a list ["repo-a"] is not yet exercised live
    permissions={
        "Contents": "write", "Pull requests": "write", "Issues": "write",
        "Workflows": "write", "Actions": "write",
        "Commit statuses": "read", "Variables": "read",
    },
    expiry_days=90,                # preset or a custom date; None = no expiry
    on_token=store_in_secret_store,  # receives the value; nothing else does
    user_data_dir=PROFILE,
)
```

- Before *Generate token*, the flow reads the form back: owner, name,
  repository access and every permission row. Any difference raises
  `GitHubTokenFlowError` and nothing is submitted. `dry_run=True` stops there.
- `Metadata: Read-only` is mandatory and is added by GitHub.
- `Checks` is not offered for fine-grained PATs, only for GitHub Apps. Asking
  for a permission the form does not offer raises.
- The value is passed to `on_token` and is not returned, printed or logged.
  `facts` holds only non-secret facts and the callback's return value.
- If the organisation requires approval, `facts["pending_approval"]` is true
  and the sync entry calls `github_approve_token_request_async` in the same
  session. That function also raises on any auth prompt.
- `github_delete_fine_grained_token_async(page, name=...)` deletes a token by
  name, for example one whose value was lost before it was stored.

The async forms take an attached `page`:
`github_create_fine_grained_token_async(page, name=..., ...)`.
