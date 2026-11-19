"""Tests for scitex_browser.content._extract_chat.

The page collaborator is injected via ``open_page``, so these exercise the
real extraction logic against a hand-rolled fake page -- no browser binary and
no mock library.
"""

import json
from contextlib import asynccontextmanager

import pytest

from scitex_browser.content._extract_chat import (
    ChatExtractionError,
    conversation_id,
    detect_provider,
    extract_chat_async,
    format_transcript,
    normalize_chatgpt_thread,
)

_CID = "6a794147-d918-83ee-9402-a509040e3470"
_URL = f"https://chatgpt.com/c/{_CID}"


def _node(role, text, created, *, content_type="text", attachments=()):
    """Build a mapping node in ChatGPT's real payload shape.

    Uploaded files live in ``metadata.attachments``; ``content.parts`` holds
    only prose and asset pointers.
    """
    return {
        "message": {
            "author": {"role": role},
            "create_time": created,
            "content": {
                "content_type": content_type,
                "parts": [text] if text else [],
            },
            "metadata": {
                "attachments": [
                    {
                        "id": f"file_{name}",
                        "name": name,
                        "mime_type": "text/markdown",
                        "size": 123,
                    }
                    for name in attachments
                ]
            },
        }
    }


def _payload(nodes, title="A thread"):
    return {"title": title, "mapping": {str(i): n for i, n in enumerate(nodes)}}


class FakePage:
    """Minimal stand-in exposing only what the extraction code calls."""

    def __init__(self, *, token="tok", status=200, body=None, url=_URL, title="T"):
        self._token = token
        self._status = status
        self._body = body if body is not None else json.dumps(_payload([]))
        self.url = url
        self._title = title
        self.evaluated = []

    async def title(self):
        return self._title

    async def evaluate(self, js, arg=None):
        self.evaluated.append((js, arg))
        if "auth/session" in js:
            return self._token
        if "backend-api/conversation" in js:
            return {"status": self._status, "body": self._body}
        if "data-message-author-role" in js:
            return [{"role": "user", "text": "from dom"}]
        raise AssertionError(f"unexpected evaluate: {js[:60]}")


def _opener(page):
    @asynccontextmanager
    async def open_page(url, *, wait_until, timeout_ms):
        yield page

    return open_page


def _two_turn_page(title="Real title"):
    body = json.dumps(
        _payload(
            [_node("user", "hi", 1.0), _node("assistant", "hello", 2.0)],
            title=title,
        )
    )
    return FakePage(body=body)


class TestDetectProvider:
    @pytest.mark.parametrize(
        "url",
        [
            "https://chatgpt.com/c/x",
            "https://chat.openai.com/c/x",
            "HTTPS://ChatGPT.com/",
        ],
    )
    def test_known_chat_host_detected_as_chatgpt(self, url):
        # Arrange
        expected = "chatgpt"
        # Act
        actual = detect_provider(url)
        # Assert
        assert actual == expected

    def test_unknown_host_detected_as_generic(self):
        # Arrange
        url = "https://example.com/thread/1"
        # Act
        actual = detect_provider(url)
        # Assert
        assert actual == "generic"


class TestConversationId:
    def test_conversation_path_yields_uuid(self):
        # Arrange
        url = _URL
        # Act
        actual = conversation_id(url)
        # Assert
        assert actual == _CID

    def test_share_path_yields_uuid(self):
        # Arrange
        url = f"https://chatgpt.com/share/{_CID}"
        # Act
        actual = conversation_id(url)
        # Assert
        assert actual == _CID

    def test_url_without_id_yields_none(self):
        # Arrange
        url = "https://chatgpt.com/"
        # Act
        actual = conversation_id(url)
        # Assert
        assert actual is None


class TestNormalizeChatgptThread:
    def test_turns_sorted_by_create_time(self):
        # Arrange
        payload = _payload(
            [
                _node("assistant", "second", 200.0),
                _node("user", "first", 100.0),
                _node("assistant", "third", 300.0),
            ]
        )
        # Act
        result = normalize_chatgpt_thread(payload)
        # Assert
        assert [t["text"] for t in result["turns"]] == ["first", "second", "third"]

    def test_reasoning_nodes_are_dropped(self):
        # Arrange: ChatGPT stores several structural nodes per assistant reply
        payload = _payload(
            [
                _node("assistant", "think", 2.0, content_type="thoughts"),
                _node("assistant", "recap", 3.0, content_type="reasoning_recap"),
                _node("assistant", "answer", 5.0),
            ]
        )
        # Act
        result = normalize_chatgpt_thread(payload)
        # Assert
        assert [t["text"] for t in result["turns"]] == ["answer"]

    def test_tool_role_nodes_are_dropped(self):
        # Arrange
        payload = _payload(
            [_node("tool", "output", 4.0), _node("assistant", "answer", 5.0)]
        )
        # Act
        result = normalize_chatgpt_thread(payload)
        # Assert
        assert [t["role"] for t in result["turns"]] == ["assistant"]

    def test_attachment_names_are_deduplicated(self):
        # Arrange
        payload = _payload(
            [
                _node("user", "a", 1.0, attachments=("BYOX.md", "TODO.md")),
                _node("user", "b", 2.0, attachments=("TODO.md",)),
            ]
        )
        # Act
        result = normalize_chatgpt_thread(payload)
        # Assert
        assert [a["name"] for a in result["attachments"]] == ["BYOX.md", "TODO.md"]

    def test_attachment_only_turn_is_kept(self):
        # Arrange: an upload with no prose is still a turn
        payload = _payload([_node("user", "", 1.0, attachments=("deck.pptx",))])
        # Act
        result = normalize_chatgpt_thread(payload)
        # Assert
        assert result["turns"][0]["attachments"][0]["name"] == "deck.pptx"

    def test_attachment_carries_file_id_for_download(self):
        # Arrange
        payload = _payload([_node("user", "a", 1.0, attachments=("TODO.md",))])
        # Act
        result = normalize_chatgpt_thread(payload)
        # Assert
        assert result["attachments"][0]["id"] == "file_TODO.md"

    def test_parts_dicts_are_not_read_as_attachments(self):
        # Arrange: files live in metadata, never in content.parts -- reading
        # parts yields no names at all, which silently emptied the inventory
        payload = _payload([_node("user", "a", 1.0)])
        node = payload["mapping"]["0"]["message"]
        node["content"]["parts"].append({"name": "not-an-attachment.md"})
        # Act
        result = normalize_chatgpt_thread(payload)
        # Assert
        assert result["attachments"] == []

    def test_empty_mapping_yields_no_turns(self):
        # Arrange
        payload = {"mapping": {}}
        # Act
        result = normalize_chatgpt_thread(payload)
        # Assert
        assert result["turns"] == []

    def test_thread_title_is_carried_through(self):
        # Arrange
        payload = _payload([_node("user", "hi", 1.0)], title="Real title")
        # Act
        result = normalize_chatgpt_thread(payload)
        # Assert
        assert result["title"] == "Real title"


class TestExtractChatAsync:
    @pytest.mark.asyncio
    async def test_api_thread_returns_every_turn(self):
        # Arrange
        page = _two_turn_page()
        # Act
        result = await extract_chat_async(_URL, wait_seconds=0, open_page=_opener(page))
        # Assert
        assert [t["text"] for t in result["turns"]] == ["hi", "hello"]

    @pytest.mark.asyncio
    async def test_api_thread_reports_chatgpt_provider(self):
        # Arrange
        page = _two_turn_page()
        # Act
        result = await extract_chat_async(_URL, wait_seconds=0, open_page=_opener(page))
        # Assert
        assert result["provider"] == "chatgpt"

    @pytest.mark.asyncio
    async def test_api_thread_reports_final_url(self):
        # Arrange
        page = _two_turn_page()
        # Act
        result = await extract_chat_async(_URL, wait_seconds=0, open_page=_opener(page))
        # Assert
        assert result["url"] == _URL

    @pytest.mark.asyncio
    async def test_missing_token_raises_extraction_error(self):
        # Arrange: no access token means the attached browser is not logged in
        page = FakePage(token="")
        # Act
        # Assert
        with pytest.raises(ChatExtractionError, match="not logged in"):
            await extract_chat_async(_URL, wait_seconds=0, open_page=_opener(page))

    @pytest.mark.asyncio
    async def test_api_error_status_raises_extraction_error(self):
        # Arrange
        page = FakePage(status=404)
        # Act
        # Assert
        with pytest.raises(ChatExtractionError, match="404"):
            await extract_chat_async(_URL, wait_seconds=0, open_page=_opener(page))

    @pytest.mark.asyncio
    async def test_url_without_conversation_id_raises(self):
        # Arrange
        page = FakePage(url="https://chatgpt.com/")
        # Act
        # Assert
        with pytest.raises(ChatExtractionError, match="no conversation id"):
            await extract_chat_async(
                "https://chatgpt.com/", wait_seconds=0, open_page=_opener(page)
            )

    @pytest.mark.asyncio
    async def test_unknown_provider_reports_generic_provider(self):
        # Arrange
        page = FakePage(url="https://example.com/thread")
        # Act
        result = await extract_chat_async(
            "https://example.com/thread", wait_seconds=0, open_page=_opener(page)
        )
        # Assert
        assert result["provider"] == "generic"

    @pytest.mark.asyncio
    async def test_unknown_provider_reads_dom_turns(self):
        # Arrange
        page = FakePage(url="https://example.com/thread")
        # Act
        result = await extract_chat_async(
            "https://example.com/thread", wait_seconds=0, open_page=_opener(page)
        )
        # Assert
        assert result["turns"][0]["text"] == "from dom"


class TestFormatTranscript:
    def test_transcript_includes_thread_title(self):
        # Arrange
        thread = {"title": "A thread", "turns": []}
        # Act
        out = format_transcript(thread)
        # Assert
        assert "# A thread" in out

    def test_transcript_includes_attachment_names(self):
        # Arrange
        thread = {
            "title": "A thread",
            "turns": [
                {
                    "role": "user",
                    "text": "ask",
                    "attachments": [{"id": "f1", "name": "BYOX.md"}],
                }
            ],
        }
        # Act
        out = format_transcript(thread)
        # Assert
        assert "attachments: BYOX.md" in out

    def test_transcript_numbers_each_turn(self):
        # Arrange
        thread = {
            "title": "A thread",
            "turns": [
                {"role": "user", "text": "ask", "attachments": []},
                {"role": "assistant", "text": "answer", "attachments": []},
            ],
        }
        # Act
        out = format_transcript(thread)
        # Assert
        assert "## 01 [assistant]" in out

    def test_untitled_thread_renders_placeholder(self):
        # Arrange
        thread = {"turns": []}
        # Act
        out = format_transcript(thread)
        # Assert
        assert "Untitled thread" in out


# EOF
