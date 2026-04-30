---
name: auth-stealth-remote
description: Auth, Stealth, Remote — see file body for details.
tags: [scitex-browser, scitex-package]
---

# Auth, Stealth, Remote

## auth — Google OAuth

```python
from scitex_browser.auth import GoogleAuthHelper, google_login

# One-shot
ok = await google_login(page, "me@gmail.com", "PASSWORD")

# Class form (reuse across flows)
auth = GoogleAuthHelper(email="me@gmail.com", password="PASSWORD")
ok = await auth.login_via_google_button(page)
```

## stealth — anti-detection

```python
from scitex_browser.stealth import StealthManager, HumanBehavior

StealthManager(page).apply()          # evaluate-on-new-document patches
HumanBehavior(page).type_like_human("hello")
HumanBehavior(page).move_mouse_to(".btn")
```

`StealthManager` applies the common set of navigator/plugin patches to
fool basic headless-detection scripts. `HumanBehavior` injects
jitter/delays to type and move the mouse like a person.

## remote — ZenRows (cloud browser) and CAPTCHA

```python
from scitex_browser.remote import (
    ZenRowsAPIBrowser,
    ZenRowsRemoteScholarBrowserManager,
    CaptchaHandler,
)

async with ZenRowsAPIBrowser(api_key=KEY) as browser:
    page = await browser.new_page()
    await page.goto("https://example.com")

# Solve / detect CAPTCHA on any page:
await CaptchaHandler(page).wait_and_solve()
```

`ZenRowsRemoteScholarBrowserManager` is the scholar-workflow-specific
wrapper that routes requests through ZenRows' proxy network and
reconstructs a Playwright-compatible page API.

## automation — cookie consent

```python
from scitex_browser.automation import CookieAutoAcceptor

CookieAutoAcceptor(page).start()   # auto-accepts common consent banners
```

Will be `None` if Playwright is not installed.
