#!/usr/bin/env python3
"""Create a GitHub fine-grained personal access token in a signed-in browser.

Drives ``github.com/settings/personal-access-tokens/new`` in a dedicated,
already signed-in Chrome profile (see ``_dedicated_profile``). The generated
value is handed to a caller-supplied callback and is never printed, logged,
returned or written by this module.

The flow never types a password and never answers 2FA: any sign-in, sudo
("Confirm access") or two-factor prompt raises ``GitHubAuthPromptError`` so a
human can complete it in an ordinary window.

Before clicking *Generate token*, the flow reads the form back (owner,
repository access, every permission row) and refuses to submit if it differs
from the request.
"""

from __future__ import annotations

import datetime as _dt
import re
from typing import Awaitable, Callable, Mapping, Optional, Sequence, Union

__all__ = [
    "GitHubAuthPromptError",
    "GitHubTokenFlowError",
    "NEW_TOKEN_URL",
    "normalize_permissions",
    "github_create_fine_grained_token",
    "github_create_fine_grained_token_async",
    "github_approve_token_request_async",
    "github_delete_fine_grained_token_async",
]

NEW_TOKEN_URL = "https://github.com/settings/personal-access-tokens/new"
READ = "Read-only"
WRITE = "Read and write"
_LEVELS = {
    "read": READ,
    "read-only": READ,
    "readonly": READ,
    "r": READ,
    "write": WRITE,
    "read and write": WRITE,
    "read-write": WRITE,
    "rw": WRITE,
}
_TOKEN_RE = re.compile(r"github_pat_[A-Za-z0-9_]{20,255}")
_AUTH_URL_MARKERS = (
    "/login",
    "/session",  # /session, /sessions/sudo, /sessions/two-factor, ...
    "/sessions/",
    "two-factor",
    "verified-device",
)


_AUTH_HEADINGS = (
    "Confirm access",
    "Two-factor authentication",
    "Sign in to GitHub",
    "Device verification",
    "Authorization failed",
)


class GitHubTokenFlowError(RuntimeError):
    """The page did not behave as the flow expects; nothing was submitted
    unless the message says so."""


class GitHubAuthPromptError(GitHubTokenFlowError):
    """GitHub asked for a password, sudo confirmation or 2FA. A human must act."""


def normalize_permissions(permissions: Mapping[str, str]) -> dict[str, str]:
    """Map {"Contents": "write", ...} to GitHub's labels; reject unknown levels.

    ``Metadata`` is mandatory read-only on GitHub and is dropped here; the
    read-back check accounts for it.
    """
    out: dict[str, str] = {}
    for name, level in permissions.items():
        key = str(level).strip().lower()
        if key not in _LEVELS:
            raise ValueError(f"unknown access level {level!r} for {name!r}")
        if name.strip().lower() == "metadata":
            if _LEVELS[key] != READ:
                raise ValueError("Metadata can only be Read-only")
            continue
        out[name.strip()] = _LEVELS[key]
    return out


def _exact(text: str) -> "re.Pattern[str]":
    return re.compile(r"^\s*" + re.escape(text) + r"\s*$")


async def assert_no_auth_prompt(page) -> None:
    """Raise GitHubAuthPromptError if the page is a sign-in/sudo/2FA prompt."""
    url = page.url
    path = url.split("github.com", 1)[-1]
    if any(m in path for m in _AUTH_URL_MARKERS):
        raise GitHubAuthPromptError(f"GitHub asked for authentication at {path}")
    if await page.locator("input[type=password]:visible").count():
        raise GitHubAuthPromptError("GitHub shows a password field")
    for marker in _AUTH_HEADINGS:
        headings = page.locator("h1, h2").filter(has_text=marker)
        for i in range(await headings.count()):
            if await headings.nth(i).is_visible():
                raise GitHubAuthPromptError(f"GitHub shows '{marker}'")


async def _select_owner(page, resource_owner: str) -> None:
    button = page.locator("#resource-owner-select-panel-button")
    if (await button.inner_text()).strip() == resource_owner:
        return
    await button.click()
    option = page.locator("[role=option]").filter(has_text=_exact(resource_owner))
    try:  # the owner list loads asynchronously after the panel opens
        await option.first.wait_for(state="visible", timeout=15_000)
    except Exception:  # noqa: BLE001 - reported below with a clear message
        pass
    if await option.count() == 0:
        raise GitHubTokenFlowError(
            f"resource owner {resource_owner!r} not offered (fine-grained PATs "
            "may be disabled for it)"
        )
    await option.first.click()
    await page.wait_for_function(
        "o => document.querySelector('#resource-owner-select-panel-button')"
        ".innerText.trim() === o",
        arg=resource_owner,
    )


def _expiry_label_prefix(days: int) -> str:
    return f"{days} days"


async def _select_expiry(page, expiry_days: Optional[int]) -> str:
    button = page.locator("button[id^=action-menu-][id$=-button]").filter(
        has_text=re.compile(r"days|expiration|Custom", re.I)
    )
    await button.first.click()
    items = page.locator("[role=menuitem]:visible, [role=menuitemradio]:visible")
    if expiry_days is None:
        await items.filter(has_text=_exact("No expiration")).first.click()
        return "No expiration"
    preset = items.filter(
        has_text=re.compile(r"^\s*" + _expiry_label_prefix(expiry_days) + r"\b")
    )
    if await preset.count():
        await preset.first.click()
    else:
        await items.filter(has_text=_exact("Custom")).first.click()
        date = (_dt.date.today() + _dt.timedelta(days=expiry_days)).isoformat()
        await page.fill("#user_programmatic_access_custom_expires_at", date)
    return (await button.first.inner_text()).strip()


async def _select_repos(page, repos: Union[str, Sequence[str]]) -> None:
    if repos == "all":
        await page.check("#install_target_all")
        return
    if repos in ("public", "none"):
        await page.check("#install_target_none")
        return
    if isinstance(repos, str):
        raise ValueError("repos must be 'all', 'public' or a list of repository names")
    await page.check("#install_target_selected")
    picker = page.get_by_role("button", name=re.compile("Select repositories", re.I))
    await picker.first.click()
    search = page.locator(
        "[role=dialog] input[type=search], [role=dialog] input[type=text]"
    ).first
    for repo in repos:
        short = repo.split("/")[-1]
        await search.fill(short)
        option = page.locator("[role=option]").filter(has_text=_exact(short))
        await option.first.wait_for(state="visible")
        await option.first.click()
    await page.keyboard.press("Escape")


_ROW_BUTTON_JS = r"""
(name) => {
  const isAccess = b => /^Access:/.test((b.innerText || '').replace(/\s+/g, ''));
  const buttons = [...document.querySelectorAll('button')].filter(isAccess);
  for (const b of buttons) {
    let n = b;
    for (let i = 0; i < 8 && n; i++) {
      n = n.parentElement;
      if (!n) break;
      if ([...n.querySelectorAll('button')].filter(isAccess).length > 1) break;
      const hit = [...n.querySelectorAll('*')].some(
        e => e.children.length === 0 && e.textContent.trim() === name);
      if (hit) {
        if (!b.id) b.id = 'stx-access-' + Math.random().toString(36).slice(2);
        return b.id;
      }
    }
  }
  return null;
}
"""

_READ_ROWS_JS = r"""
() => {
  const isAccess = b => /^Access:/.test((b.innerText || '').replace(/\s+/g, ''));
  const rows = [];
  for (const b of [...document.querySelectorAll('button')].filter(isAccess)) {
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    let n = b, row = b;
    for (let i = 0; i < 8 && n; i++) {
      n = n.parentElement;
      if (!n) break;
      if ([...n.querySelectorAll('button')].filter(isAccess).length > 1) break;
      row = n;
    }
    const texts = [...row.querySelectorAll('*')]
      .filter(e => e.children.length === 0 && !b.contains(e) && e.textContent.trim())
      .map(e => e.textContent.trim());
    for (const e of row.querySelectorAll('[aria-label]'))
      texts.push(e.getAttribute('aria-label').trim());
    rows.push({level: (b.innerText || '').replace(/^\s*Access:\s*/, '').trim(), texts});
  }
  return rows;
}
"""


async def _add_permissions(page, wanted: Mapping[str, str]) -> None:
    await page.get_by_role("button", name="Add permissions").first.click()
    await page.locator("li[role=option]").first.wait_for(state="visible")
    for name in wanted:
        option = page.locator("li[role=option]").filter(has_text=_exact(name))
        if await option.count() == 0:
            await page.keyboard.press("Escape")
            raise GitHubTokenFlowError(
                f"permission {name!r} is not offered for fine-grained tokens"
            )
        if (await option.first.get_attribute("aria-selected")) != "true":
            await option.first.click()
    await page.keyboard.press("Escape")
    for name, level in wanted.items():
        button_id = await page.evaluate(_ROW_BUTTON_JS, name)
        if not button_id:
            raise GitHubTokenFlowError(f"no access control found for {name!r}")
        button = page.locator(f"[id='{button_id}']")
        current = re.sub(r"^\s*Access:\s*", "", await button.inner_text()).strip()
        if current == level:
            continue
        await button.click()
        await (
            page.locator("[role=menuitem]:visible, [role=menuitemradio]:visible")
            .filter(has_text=_exact(level))
            .first.click()
        )


def _row_label(texts: Sequence[str]) -> Optional[str]:
    """Name a permission row from its leaf texts.

    Removable rows carry a "Remove <name>" control; the mandatory Metadata row
    has no remove control but shows its name as a leaf.
    """
    for t in texts:
        if t.startswith("Remove ") and len(t) > 7:
            return t[7:].strip()
    if "Metadata" in texts:
        return "Metadata"
    return texts[0] if texts else None


async def read_permission_rows(page) -> dict[str, str]:
    """Read back {permission: level} for every visible permission row."""
    rows = await page.evaluate(_READ_ROWS_JS)
    return {_row_label(r["texts"]): r["level"] for r in rows}


def _diff_rows(rows: Mapping[str, str], wanted: Mapping[str, str]) -> list[str]:
    expected = dict(wanted)
    expected["Metadata"] = READ
    problems = []
    for name, level in expected.items():
        if rows.get(name) != level:
            problems.append(f"{name}: want {level!r}, form has {rows.get(name)!r}")
    for name in rows:
        if name not in expected:
            problems.append(f"unexpected permission row {name!r}={rows[name]!r}")
    return problems


async def _extract_token(page) -> str:
    """Find the freshly generated value on the result page (DOM only)."""
    value = await page.evaluate(
        r"""() => {
          const re = /github_pat_[A-Za-z0-9_]{20,255}/;
          for (const el of document.querySelectorAll('input, textarea')) {
            const m = (el.value || '').match(re); if (m) return m[0];
          }
          for (const el of document.querySelectorAll('[value]')) {
            const m = (el.getAttribute('value') || '').match(re); if (m) return m[0];
          }
          const m = (document.body.innerText || '').match(re);
          return m ? m[0] : null;
        }"""
    )
    if not value or not _TOKEN_RE.fullmatch(value):
        raise GitHubTokenFlowError(
            "token was submitted but no value was found on the result page; "
            "check github.com/settings/personal-access-tokens and regenerate"
        )
    return value


async def github_create_fine_grained_token_async(
    page,
    *,
    name: str,
    resource_owner: str,
    permissions: Mapping[str, str],
    on_token: Callable[[str], Union[None, object, Awaitable[object]]],
    repos: Union[str, Sequence[str]] = "all",
    expiry_days: Optional[int] = 90,
    description: Optional[str] = None,
    dry_run: bool = False,
    timeout_ms: int = 30_000,
) -> dict:
    """Create the token on an attached, signed-in ``page``.

    ``on_token(value)`` receives the generated value; its return value is
    passed back as ``result["callback"]``. The value itself is never returned.
    With ``dry_run`` the form is filled and verified but not submitted.

    Returns a dict of non-secret facts (name, owner, expiry label, permission
    rows read back from the form, whether approval is pending).
    """
    wanted = normalize_permissions(permissions)
    page.set_default_timeout(timeout_ms)
    await page.goto(NEW_TOKEN_URL, wait_until="domcontentloaded")
    await assert_no_auth_prompt(page)
    await page.locator("#user_programmatic_access_name").wait_for(state="visible")

    await page.fill("#user_programmatic_access_name", name)
    if description:
        await page.fill("#user_programmatic_access_description", description)
    await _select_owner(page, resource_owner)
    expiry_label = await _select_expiry(page, expiry_days)
    await _select_repos(page, repos)
    await _add_permissions(page, wanted)

    rows = await read_permission_rows(page)
    problems = _diff_rows(rows, wanted)
    owner_now = (await page.inner_text("#resource-owner-select-panel-button")).strip()
    if owner_now != resource_owner:
        problems.append(f"owner: want {resource_owner!r}, form has {owner_now!r}")
    if (await page.input_value("#user_programmatic_access_name")) != name:
        problems.append("token name did not stick")
    if repos == "all" and not await page.is_checked("#install_target_all"):
        problems.append("'All repositories' is not selected")
    if problems:
        raise GitHubTokenFlowError("form read-back mismatch: " + "; ".join(problems))

    facts = {
        "name": name,
        "resource_owner": resource_owner,
        "expiry": expiry_label,
        "repos": repos if isinstance(repos, str) else list(repos),
        "permissions": rows,
        "submitted": False,
    }
    if dry_run:
        return facts

    await page.get_by_role("button", name="Generate token").first.click()
    title = page.locator("#fgpat-confirmation-dialog-title")
    try:
        await title.wait_for(state="visible", timeout=5_000)
    except Exception:  # noqa: BLE001 - some layouts submit without a dialog
        pass
    await assert_no_auth_prompt(page)
    submit = page.locator("button[type=submit]:visible").filter(
        has_text=_exact("Generate token")
    )
    if await submit.count():
        await submit.first.click()
    await page.wait_for_load_state("domcontentloaded")
    # The value is rendered in an input / clipboard-copy ``value`` attribute,
    # not necessarily in innerText, so look in all three places.
    await page.wait_for_function(
        """() => {
          const re = /github_pat_/;
          if (re.test(document.body.innerText)) return true;
          for (const el of document.querySelectorAll('input, textarea'))
            if (re.test(el.value || '')) return true;
          for (const el of document.querySelectorAll('[value]'))
            if (re.test(el.getAttribute('value') || '')) return true;
          return !!document.querySelector('input[type=password]') ||
                 /\\/sessions?\\//.test(location.pathname);
        }""",
        timeout=60_000,
    )
    await assert_no_auth_prompt(page)
    facts["submitted"] = True

    value = await _extract_token(page)
    try:
        result = on_token(value)
        if hasattr(result, "__await__"):
            result = await result
    finally:
        del value
    facts["callback"] = result
    body = await page.inner_text("body")
    facts["pending_approval"] = bool(
        re.search(r"pending|awaiting approval", body, re.I)
    )
    return facts


async def github_delete_fine_grained_token_async(
    page, *, name: str, timeout_ms: int = 30_000
) -> bool:
    """Delete the account's fine-grained token called ``name``.

    Returns False if no token has that name. Raises on any auth prompt.
    """
    page.set_default_timeout(timeout_ms)
    await page.goto(
        "https://github.com/settings/personal-access-tokens",
        wait_until="domcontentloaded",
    )
    await assert_no_auth_prompt(page)
    link = page.get_by_role("link", name=_exact(name))
    if await link.count() != 1:
        return False
    await link.first.click()
    await page.wait_for_load_state("domcontentloaded")
    await assert_no_auth_prompt(page)
    await page.get_by_role("button", name=re.compile(r"^\s*Delete", re.I)).first.click()
    confirm = page.locator("[role=dialog]:visible, dialog[open]").get_by_role(
        "button", name=re.compile(r"I understand|Delete", re.I)
    )
    await confirm.last.wait_for(state="visible")
    await confirm.last.click()
    await page.wait_for_load_state("domcontentloaded")
    await assert_no_auth_prompt(page)
    await page.goto(
        "https://github.com/settings/personal-access-tokens",
        wait_until="domcontentloaded",
    )
    return await page.get_by_role("link", name=_exact(name)).count() == 0


async def github_approve_token_request_async(
    page, *, org: str, token_name: str, timeout_ms: int = 30_000
) -> bool:
    """Approve a pending fine-grained PAT request in an org (owner session).

    Returns False if no pending request with that token name exists.
    """
    page.set_default_timeout(timeout_ms)
    await page.goto(
        f"https://github.com/organizations/{org}/settings/personal-access-token-requests",
        wait_until="domcontentloaded",
    )
    await assert_no_auth_prompt(page)
    link = page.get_by_role("link", name=_exact(token_name))
    if await link.count() == 0:
        return False
    await link.first.click()
    await page.wait_for_load_state("domcontentloaded")
    await assert_no_auth_prompt(page)
    await page.get_by_role(
        "button", name=re.compile(r"^\s*Approve", re.I)
    ).first.click()
    confirm = page.locator("[role=dialog]:visible").get_by_role(
        "button", name=re.compile(r"Approve", re.I)
    )
    if await confirm.count():
        await confirm.first.click()
    await page.wait_for_load_state("domcontentloaded")
    await assert_no_auth_prompt(page)
    return True


def github_create_fine_grained_token(
    name: str,
    resource_owner: str,
    repos: Union[str, Sequence[str]] = "all",
    permissions: Optional[Mapping[str, str]] = None,
    expiry_days: Optional[int] = 90,
    *,
    on_token: Callable[[str], object],
    user_data_dir: str,
    description: Optional[str] = None,
    approve_if_pending: bool = True,
    close_after: bool = True,
    dry_run: bool = False,
) -> dict:
    """Synchronous entry point: launch the dedicated profile, create, close.

    Closes the headless instance afterwards only if this call launched it.
    """
    import asyncio

    from ._dedicated_profile import attached_page, launch_dedicated_chrome

    if not permissions:
        raise ValueError("permissions must name at least one permission")
    chrome = launch_dedicated_chrome(user_data_dir)

    async def _run() -> dict:
        async with attached_page(chrome.cdp_url) as page:
            await page.set_viewport_size({"width": 1280, "height": 900})
            facts = await github_create_fine_grained_token_async(
                page,
                name=name,
                resource_owner=resource_owner,
                permissions=permissions,
                on_token=on_token,
                repos=repos,
                expiry_days=expiry_days,
                description=description,
                dry_run=dry_run,
            )
            if facts.get("pending_approval") and approve_if_pending:
                facts["approved"] = await github_approve_token_request_async(
                    page, org=resource_owner, token_name=name
                )
            return facts

    try:
        return asyncio.run(_run())
    finally:
        if close_after:
            chrome.close()
