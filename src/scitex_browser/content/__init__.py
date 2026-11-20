#!/usr/bin/env python3
# SciTeX Browser Content Capture
# ----------------------------------------

from ._extract_chat import (
    DEFAULT_CDP_URL,
    ChatExtractionError,
    attach_cdp_page,
    conversation_id,
    detect_provider,
    extract_chat,
    extract_chat_async,
    format_transcript,
    normalize_chatgpt_thread,
)
from ._fetch_content import (
    extract_from_page_async,
    fetch_content,
    fetch_content_async,
    get_html,
    get_html_async,
    get_text,
    get_text_async,
    save_as_html,
    save_as_html_async,
    save_as_text,
    save_as_text_async,
)

__all__ = [
    "DEFAULT_CDP_URL",
    "ChatExtractionError",
    "attach_cdp_page",
    "conversation_id",
    "detect_provider",
    "extract_chat",
    "extract_chat_async",
    "extract_from_page_async",
    "format_transcript",
    "normalize_chatgpt_thread",
    "fetch_content",
    "fetch_content_async",
    "get_html",
    "get_html_async",
    "get_text",
    "get_text_async",
    "save_as_html",
    "save_as_html_async",
    "save_as_text",
    "save_as_text_async",
]

# EOF
