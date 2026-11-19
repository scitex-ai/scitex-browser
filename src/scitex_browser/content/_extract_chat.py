#!/usr/bin/env python3
"""Extract a chat thread (messages plus attachment names) from a chat web app.

Chat UIs virtualize their message lists: only the messages near the viewport
exist in the DOM, so reading ``document.body.innerText`` returns whatever
happened to be rendered and silently omits the rest. Measured against one
ChatGPT thread, the DOM held 6 messages while the site's own API returned 25 --
a scrape would have looked complete and been wrong.

So provider-specific extraction is the point of this module, not an
optimization: where a site exposes its own conversation API, this reads that
and falls back to the DOM only for providers it does not know.

Reading a logged-in thread needs a logged-in browser, which means attaching
over the Chrome DevTools Protocol to a Chrome the user has already
authenticated -- see :func:`attach_cdp_page`.
"""

import asyncio
import re
from contextlib import asynccontextmanager
from typing import Literal

from .._page_prep import normalize_url

WaitUntil = Literal["commit", "domcontentloaded", "load", "networkidle"]

DEFAULT_CDP_URL = "http://127.0.0.1:9222"

_DEFAULT_NAV_TIMEOUT_MS = 60_000

# ChatGPT mints a short-lived bearer token for its own backend from the
# session cookie; every backend-api call needs it.
_CHATGPT_TOKEN_JS = """
async () => {
  const r = await fetch('/api/auth/session', {credentials: 'include'});
  if (!r.ok) return '';
  const j = await r.json();
  return j.accessToken || '';
}
"""

_CHATGPT_CONVERSATION_JS = """
async ([cid, token]) => {
  const r = await fetch('/backend-api/conversation/' + cid, {
    credentials: 'include',
    headers: {Authorization: 'Bearer ' + token},
  });
  return {status: r.status, body: await r.text()};
}
"""

# Fallback only: whatever the DOM currently holds, which for a virtualized
# thread is a subset of the conversation.
_DOM_TURNS_JS = """
() => [...document.querySelectorAll('[data-message-author-role]')].map(n => ({
  role: n.getAttribute('data-message-author-role'),
  text: n.innerText,
}))
"""

_CHATGPT_HOSTS = ("chatgpt.com", "chat.openai.com")

_CONVERSATION_ID_RE = re.compile(
    r"/c/([0-9a-fA-F-]{36})|/share/([0-9a-fA-F-]{36})",
)


class ChatExtractionError(RuntimeError):
    """Raised when a thread cannot be read -- never returns partial content."""


def detect_provider(url: str) -> str:
    """Return the provider key for ``url`` (``"chatgpt"`` or ``"generic"``)."""
    lowered = url.lower()
    if any(host in lowered for host in _CHATGPT_HOSTS):
        return "chatgpt"
    return "generic"


def conversation_id(url: str) -> str | None:
    """Pull the conversation UUID out of a chat URL, if it carries one."""
    match = _CONVERSATION_ID_RE.search(url)
    if not match:
        return None
    return match.group(1) or match.group(2)


@asynccontextmanager
async def attach_cdp_page(
    url: str,
    *,
    wait_until: WaitUntil = "domcontentloaded",
    timeout_ms: int = _DEFAULT_NAV_TIMEOUT_MS,
    cdp_url: str = DEFAULT_CDP_URL,
):
    """Yield a page in an already-running, already-authenticated Chrome.

    The browser must have been started with ``--remote-debugging-port``; Chrome
    cannot enable that on a live process, and refuses it entirely for the
    default profile directory.

    This reuses the user's own browser, so it deliberately does **not** close
    the browser or the page on exit -- only the Playwright connection.
    """
    from playwright.async_api import async_playwright

    pw = await async_playwright().start()
    try:
        try:
            browser = await pw.chromium.connect_over_cdp(cdp_url)
        except Exception as exc:  # noqa: BLE001 - surfaced as a usage error
            raise ChatExtractionError(
                f"no debuggable Chrome at {cdp_url}: {exc}. Start one with "
                "--remote-debugging-port and log in, then retry."
            ) from exc

        contexts = browser.contexts
        if not contexts:
            raise ChatExtractionError(f"browser at {cdp_url} has no context")
        context = contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        yield page
    finally:
        await pw.stop()


def _attachments_of(message: dict) -> list:
    """Read a message's uploaded files.

    These live in ``metadata.attachments``, *not* in ``content.parts`` -- the
    parts hold prose and asset pointers, so reading them yields no file names
    at all.
    """
    raw = (message.get("metadata") or {}).get("attachments") or []
    return [
        {
            "id": item.get("id"),
            "name": item.get("name"),
            "mime_type": item.get("mime_type"),
            "size": item.get("size"),
        }
        for item in raw
        if isinstance(item, dict) and item.get("name")
    ]


def normalize_chatgpt_thread(payload: dict) -> dict:
    """Flatten a ChatGPT ``/backend-api/conversation`` payload into turns.

    Keeps only user and assistant prose. Tool calls, reasoning traces and
    recaps are structural noise for a transcript, and ChatGPT stores several
    per assistant reply.
    """
    rows = []
    for node in (payload.get("mapping") or {}).values():
        message = node.get("message")
        if not message:
            continue
        role = (message.get("author") or {}).get("role")
        if role not in ("user", "assistant"):
            continue
        content = message.get("content") or {}
        if content.get("content_type") not in ("text", "multimodal_text"):
            continue

        parts = content.get("parts") or []
        text = "".join(p for p in parts if isinstance(p, str)).strip()
        attachments = _attachments_of(message)
        if not text and not attachments:
            continue

        rows.append(
            {
                "created": message.get("create_time") or 0.0,
                "role": role,
                "text": text,
                "attachments": attachments,
            }
        )

    rows.sort(key=lambda row: row["created"])

    seen = []
    seen_ids = set()
    for row in rows:
        for item in row["attachments"]:
            key = item.get("id") or item.get("name")
            if key not in seen_ids:
                seen_ids.add(key)
                seen.append(item)

    return {
        "provider": "chatgpt",
        "title": payload.get("title"),
        "turns": rows,
        "attachments": seen,
    }


async def extract_chatgpt_async(page, conv_id: str) -> dict:
    """Read a full ChatGPT thread through the site's own conversation API."""
    token = await page.evaluate(_CHATGPT_TOKEN_JS)
    if not token:
        raise ChatExtractionError(
            "ChatGPT session has no access token -- the attached browser is "
            "not logged in."
        )

    result = await page.evaluate(_CHATGPT_CONVERSATION_JS, [conv_id, token])
    if result.get("status") != 200:
        raise ChatExtractionError(
            f"conversation {conv_id} returned HTTP {result.get('status')}"
        )

    import json

    return normalize_chatgpt_thread(json.loads(result["body"]))


async def extract_generic_async(page) -> dict:
    """Read whatever chat-shaped turns the DOM currently exposes.

    Only a fallback: a virtualized thread yields the rendered window, not the
    conversation, so the caller is told which provider produced the result.
    """
    turns = await page.evaluate(_DOM_TURNS_JS)
    return {
        "provider": "generic",
        "title": await page.title(),
        "turns": [
            {"created": 0.0, "role": t["role"], "text": t["text"], "attachments": []}
            for t in turns
        ],
        "attachments": [],
    }


async def extract_chat_async(
    url: str,
    *,
    cdp_url: str = DEFAULT_CDP_URL,
    wait_seconds: float = 3,
    timeout_ms: int = _DEFAULT_NAV_TIMEOUT_MS,
    open_page=None,
) -> dict:
    """Extract a chat thread from ``url`` using an authenticated browser.

    Parameters
    ----------
    url : str
        Thread URL. A missing scheme is filled in as ``https://``.
    cdp_url : str
        DevTools endpoint of a logged-in Chrome to attach to.
    wait_seconds : float
        Extra seconds after navigation, for late-rendering JS.
    timeout_ms : int
        Navigation timeout in milliseconds.
    open_page : callable or None
        Injected async context manager ``open_page(url, *, wait_until,
        timeout_ms)`` yielding a navigated page. Defaults to
        :func:`attach_cdp_page`; tests pass a stand-in.

    Returns
    -------
    dict
        ``{"provider", "url", "title", "turns", "attachments"}`` where each
        turn is ``{"created", "role", "text", "attachments"}``.

    Raises
    ------
    ChatExtractionError
        If no debuggable browser is reachable, the session is not logged in,
        or the thread cannot be read. Never returns a partial thread.
    """
    url = normalize_url(url)
    provider = detect_provider(url)

    if open_page is None:

        @asynccontextmanager
        async def _attach(url, *, wait_until, timeout_ms):
            async with attach_cdp_page(
                url, wait_until=wait_until, timeout_ms=timeout_ms, cdp_url=cdp_url
            ) as page:
                yield page

        open_page = _attach

    async with open_page(
        url, wait_until="domcontentloaded", timeout_ms=timeout_ms
    ) as page:
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        if provider == "chatgpt":
            conv_id = conversation_id(page.url) or conversation_id(url)
            if conv_id is None:
                raise ChatExtractionError(f"no conversation id in URL: {url!r}")
            result = await extract_chatgpt_async(page, conv_id)
        else:
            result = await extract_generic_async(page)

        result["url"] = page.url
        return result


def extract_chat(url: str, **kwargs) -> dict:
    """Sync wrapper for :func:`extract_chat_async`."""
    return asyncio.run(extract_chat_async(url, **kwargs))


def format_transcript(thread: dict) -> str:
    """Render an extracted thread as markdown."""
    lines = [f"# {thread.get('title') or 'Untitled thread'}", ""]
    if thread.get("url"):
        lines += [f"Source: {thread['url']}", ""]

    for index, turn in enumerate(thread.get("turns") or []):
        head = f"## {index:02d} [{turn['role']}]"
        names = [a.get("name") for a in turn.get("attachments") or [] if a.get("name")]
        if names:
            head += "  attachments: " + ", ".join(names)
        lines += [head, turn.get("text") or "", ""]

    return "\n".join(lines)


# EOF
