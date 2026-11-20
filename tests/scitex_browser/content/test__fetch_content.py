"""Tests for scitex_browser.content._fetch_content.

The page collaborator is injected via ``open_page``, so these exercise the
real extraction logic against a hand-rolled fake page — no browser binary and
no mock library.
"""

from contextlib import asynccontextmanager
from pathlib import Path

import pytest

_HTML = "<html><body><p>hello</p></body></html>"
_TEXT = "hello"
_TITLE = "Example"
_FINAL_URL = "https://example.com/final"


class FakeElement:
    """Stands in for a Playwright locator's first match."""

    def __init__(self, *, count=1, html="<p>scoped</p>", text="scoped"):
        self._count = count
        self._html = html
        self._text = text

    async def count(self):
        return self._count

    async def inner_html(self):
        return self._html

    async def inner_text(self):
        return self._text

    async def is_visible(self, timeout=None):
        return False

    async def click(self, timeout=None):
        raise AssertionError("no visible consent button should be clicked")


class FakeLocator:
    def __init__(self, element):
        self.first = element


class FakePage:
    """Minimal stand-in exposing only what the extraction code calls."""

    def __init__(
        self,
        *,
        html=_HTML,
        text=_TEXT,
        title=_TITLE,
        url=_FINAL_URL,
        element=None,
        goto_error=None,
        content_error=None,
    ):
        self._html = html
        self._text = text
        self._title = title
        self.url = url
        self._element = element if element is not None else FakeElement()
        self._goto_error = goto_error
        self._content_error = content_error
        self.evaluated = []
        self.waited_ms = []
        self.navigations = []
        self.content_reads = 0

    async def goto(self, url, wait_until=None, timeout=None):
        self.navigations.append(
            {"url": url, "wait_until": wait_until, "timeout": timeout}
        )
        if self._goto_error is not None:
            raise self._goto_error

    async def content(self):
        self.content_reads += 1
        if self._content_error is not None:
            raise self._content_error
        return self._html

    async def title(self):
        return self._title

    async def evaluate(self, script):
        self.evaluated.append(script)
        return self._text

    async def wait_for_timeout(self, ms):
        self.waited_ms.append(ms)

    def locator(self, selector):
        return FakeLocator(self._element)


class FakeBrowser:
    """Tracks that the page source is closed exactly once."""

    def __init__(self, page):
        self.page = page
        self.closes = 0

    def open_page(self):
        @asynccontextmanager
        async def _open(url, *, wait_until, timeout_ms):
            # goto lives inside the try so cleanup runs on a navigation
            # failure too — same shape as the real _chromium_page.
            try:
                await self.page.goto(url, wait_until=wait_until, timeout=timeout_ms)
                yield self.page
            finally:
                self.closes += 1

        return _open


def _opener(page):
    """Build an ``open_page`` callable backed by ``page``."""
    return FakeBrowser(page).open_page()


def test_fetch_content_returns_all_four_fields():
    """fetch_content surfaces url, title, html and text from the page."""
    # Arrange
    page = FakePage()
    from scitex_browser.content import fetch_content

    # Act
    result = fetch_content("example.com", wait_seconds=0, open_page=_opener(page))

    # Assert
    assert result == {
        "url": _FINAL_URL,
        "title": _TITLE,
        "html": _HTML,
        "text": _TEXT,
    }


def test_fetch_content_adds_https_scheme_when_missing():
    """A bare host is navigated to as https://."""
    # Arrange
    page = FakePage()
    from scitex_browser.content import fetch_content

    # Act
    fetch_content("example.com", wait_seconds=0, open_page=_opener(page))

    # Assert
    assert page.navigations[0]["url"] == "https://example.com"


def test_fetch_content_preserves_an_explicit_scheme():
    """An http:// URL is not rewritten to https://."""
    # Arrange
    page = FakePage()
    from scitex_browser.content import fetch_content

    # Act
    fetch_content("http://example.com", wait_seconds=0, open_page=_opener(page))

    # Assert
    assert page.navigations[0]["url"] == "http://example.com"


def test_fetch_content_propagates_navigation_errors():
    """A navigation failure surfaces to the caller rather than returning empty."""
    # Arrange
    page = FakePage(goto_error=RuntimeError("boom"))
    browser = FakeBrowser(page)
    from scitex_browser.content import fetch_content

    # Act
    call = lambda: fetch_content(  # noqa: E731
        "example.com", wait_seconds=0, open_page=browser.open_page()
    )

    # Assert
    with pytest.raises(RuntimeError, match="boom"):
        call()


def test_fetch_content_closes_page_source_when_extraction_fails():
    """An error while reading the page must still exit the page context.

    This pins fetch_content_async's use of ``async with`` on the injected
    opener: without it, a mid-extraction failure would leak the browser.
    """
    # Arrange
    page = FakePage(content_error=RuntimeError("read failed"))
    browser = FakeBrowser(page)
    from scitex_browser.content import fetch_content

    # Act
    try:
        fetch_content("example.com", wait_seconds=0, open_page=browser.open_page())
    except RuntimeError:
        pass

    # Assert
    assert browser.closes == 1


def test_fetch_content_skips_overlay_dismissal_by_default():
    """Overlay removal is opt-in: the sweep can delete real content."""
    # Arrange
    page = FakePage()
    from scitex_browser.content import fetch_content

    # Act
    fetch_content("example.com", wait_seconds=0, open_page=_opener(page))

    # Assert — only the innerText read, no overlay-removal script
    assert len(page.evaluated) == 1


def test_fetch_content_dismisses_overlays_when_requested():
    """--dismiss-overlays runs the overlay sweep before reading."""
    # Arrange
    page = FakePage()
    from scitex_browser.content import fetch_content

    # Act
    fetch_content(
        "example.com", wait_seconds=0, dismiss_overlays=True, open_page=_opener(page)
    )

    # Assert — overlay-removal script plus the innerText read
    assert len(page.evaluated) == 2


def test_fetch_content_with_selector_returns_scoped_html():
    """A selector narrows the captured html to the matching element."""
    # Arrange
    page = FakePage(element=FakeElement(html="<p>scoped</p>"))
    from scitex_browser.content import fetch_content

    # Act
    result = fetch_content(
        "example.com", wait_seconds=0, selector="#results", open_page=_opener(page)
    )

    # Assert
    assert result["html"] == "<p>scoped</p>"


def test_fetch_content_with_selector_returns_scoped_text():
    """A selector narrows the captured text to the matching element."""
    # Arrange
    page = FakePage(element=FakeElement(text="scoped"))
    from scitex_browser.content import fetch_content

    # Act
    result = fetch_content(
        "example.com", wait_seconds=0, selector="#results", open_page=_opener(page)
    )

    # Assert
    assert result["text"] == "scoped"


def test_fetch_content_with_selector_does_not_read_whole_document():
    """Scoped capture skips the full-page content() read."""
    # Arrange
    page = FakePage()
    from scitex_browser.content import fetch_content

    # Act
    fetch_content(
        "example.com", wait_seconds=0, selector="#results", open_page=_opener(page)
    )

    # Assert
    assert page.content_reads == 0


def test_fetch_content_raises_when_selector_matches_nothing():
    """A selector matching nothing is an error, not a silent empty capture."""
    # Arrange
    page = FakePage(element=FakeElement(count=0))
    from scitex_browser.content import fetch_content

    # Act / Assert is a single raises-block, so the marker order still holds
    # Act
    call = lambda: fetch_content(  # noqa: E731
        "example.com", wait_seconds=0, selector="#missing", open_page=_opener(page)
    )

    # Assert
    with pytest.raises(ValueError, match="matched no element"):
        call()


def test_get_html_returns_only_the_markup():
    """get_html picks the html field out of fetch_content."""
    # Arrange
    page = FakePage()
    from scitex_browser.content import get_html

    # Act
    result = get_html("example.com", wait_seconds=0, open_page=_opener(page))

    # Assert
    assert result == _HTML


def test_get_text_returns_only_the_visible_text():
    """get_text picks the text field out of fetch_content."""
    # Arrange
    page = FakePage()
    from scitex_browser.content import get_text

    # Act
    result = get_text("example.com", wait_seconds=0, open_page=_opener(page))

    # Assert
    assert result == _TEXT


def test_save_as_html_normalizes_the_extension(tmp_path):
    """save_as_html forces a .html suffix even when asked for another."""
    # Arrange
    page = FakePage()
    from scitex_browser.content import save_as_html

    # Act
    result = save_as_html(
        "example.com",
        str(tmp_path / "nested" / "page.pdf"),
        wait_seconds=0,
        open_page=_opener(page),
    )

    # Assert
    assert result.endswith("page.html")


def test_save_as_html_writes_the_markup(tmp_path):
    """save_as_html persists exactly the captured html."""
    # Arrange
    page = FakePage()
    from scitex_browser.content import save_as_html

    # Act
    result = save_as_html(
        "example.com",
        str(tmp_path / "page.html"),
        wait_seconds=0,
        open_page=_opener(page),
    )

    # Assert
    assert Path(result).read_text(encoding="utf-8") == _HTML


def test_save_as_text_normalizes_the_extension(tmp_path):
    """save_as_text forces a .txt suffix even when asked for another."""
    # Arrange
    page = FakePage()
    from scitex_browser.content import save_as_text

    # Act
    result = save_as_text(
        "example.com",
        str(tmp_path / "page.md"),
        wait_seconds=0,
        open_page=_opener(page),
    )

    # Assert
    assert result.endswith("page.txt")


def test_save_as_text_writes_the_visible_text(tmp_path):
    """save_as_text persists exactly the captured text."""
    # Arrange
    page = FakePage()
    from scitex_browser.content import save_as_text

    # Act
    result = save_as_text(
        "example.com",
        str(tmp_path / "page.txt"),
        wait_seconds=0,
        open_page=_opener(page),
    )

    # Assert
    assert Path(result).read_text(encoding="utf-8") == _TEXT


def test_save_as_text_creates_missing_parent_directories(tmp_path):
    """A nested output path is created rather than raising."""
    # Arrange
    page = FakePage()
    from scitex_browser.content import save_as_text

    # Act
    result = save_as_text(
        "example.com",
        str(tmp_path / "a" / "b" / "page.txt"),
        wait_seconds=0,
        open_page=_opener(page),
    )

    # Assert
    assert Path(result).exists()


def test_content_helpers_are_exported_from_package_root():
    """The capture helpers are importable from scitex_browser directly."""
    # Arrange
    import scitex_browser

    names = ("fetch_content", "get_html", "get_text", "save_as_html", "save_as_text")

    # Act
    exported = [n for n in names if n in scitex_browser.__all__]

    # Assert
    assert exported == list(names)


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__)])

# EOF
