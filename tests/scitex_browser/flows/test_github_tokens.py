"""Offline tests for the GitHub fine-grained token flow (no network, no browser)."""

import asyncio

import pytest

from scitex_browser.flows import github_tokens as gt

SETTINGS_URL = "https://github.com/settings/personal-access-tokens/new"


class _Loc:
    def __init__(self, n=0, visible=True):
        self._n = n
        self._visible = visible

    async def count(self):
        return self._n

    def filter(self, **_kw):
        return self

    def nth(self, _i):
        return self

    async def is_visible(self):
        return self._visible


class _Page:
    """Hand-rolled async page double for the auth guard and value extraction."""

    def __init__(self, url, password=0, headings=0, js_value=None):
        self.url = url
        self._password = password
        self._headings = headings
        self._js_value = js_value

    def locator(self, sel):
        return _Loc(self._password if "password" in sel else self._headings)

    async def evaluate(self, _js, *_a):
        return self._js_value


def _run(coro):
    return asyncio.run(coro)


def test_normalize_permissions_maps_levels_and_drops_metadata():
    # Arrange
    perms = {"Contents": "write", "Variables": "read", "Metadata": "read"}
    # Act
    got = gt.normalize_permissions(perms)
    # Assert
    assert got == {"Contents": gt.WRITE, "Variables": gt.READ}


@pytest.mark.parametrize("perms", [{"Contents": "admin"}, {"Metadata": "write"}])
def test_normalize_permissions_rejects_invalid_levels(perms):
    # Arrange
    request = perms
    # Act
    call = lambda: gt.normalize_permissions(request)  # noqa: E731
    # Assert
    with pytest.raises(ValueError):
        call()


def test_diff_rows_accepts_exact_match_with_metadata():
    # Arrange
    rows = {"Contents": gt.WRITE, "Metadata": gt.READ}
    # Act
    problems = gt._diff_rows(rows, {"Contents": gt.WRITE})
    # Assert
    assert problems == []


def test_diff_rows_flags_wrong_level():
    # Arrange
    rows = {"Contents": gt.READ, "Metadata": gt.READ}
    # Act
    problems = gt._diff_rows(rows, {"Contents": gt.WRITE})
    # Assert
    assert any("Contents" in p for p in problems)


def test_diff_rows_flags_unrequested_rows():
    # Arrange
    rows = {"Contents": gt.WRITE, "Metadata": gt.READ, "Administration": gt.WRITE}
    # Act
    problems = gt._diff_rows(rows, {"Contents": gt.WRITE})
    # Assert
    assert any("Administration" in p for p in problems)


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/sessions/sudo",
        "https://github.com/login?return_to=x",
        "https://github.com/sessions/two-factor/app",
        "https://github.com/session",
    ],
)
def test_auth_prompt_urls_raise(url):
    # Arrange
    page = _Page(url)
    # Act
    call = lambda: _run(gt.assert_no_auth_prompt(page))  # noqa: E731
    # Assert
    with pytest.raises(gt.GitHubAuthPromptError):
        call()


@pytest.mark.parametrize("kw", [{"password": 1}, {"headings": 1}])
def test_password_field_or_confirm_heading_raises(kw):
    # Arrange
    page = _Page(SETTINGS_URL, **kw)
    # Act
    call = lambda: _run(gt.assert_no_auth_prompt(page))  # noqa: E731
    # Assert
    with pytest.raises(gt.GitHubAuthPromptError):
        call()


def test_settings_page_passes_auth_guard():
    # Arrange
    page = _Page(SETTINGS_URL)
    # Act
    result = _run(gt.assert_no_auth_prompt(page))
    # Assert
    assert result is None


def test_extract_token_returns_well_formed_value():
    # Arrange
    value = "github_pat_" + "A1_" * 20
    # Act
    got = _run(gt._extract_token(_Page("u", js_value=value)))
    # Assert
    assert got == value


@pytest.mark.parametrize("bad", [None, "ghp_classic", "github_pat_short"])
def test_extract_token_rejects_missing_or_malformed(bad):
    # Arrange
    page = _Page("u", js_value=bad)
    # Act
    call = lambda: _run(gt._extract_token(page))  # noqa: E731
    # Assert
    with pytest.raises(gt.GitHubTokenFlowError):
        call()


def test_extract_error_message_never_contains_the_value():
    # Arrange
    partial = "github_pat_" + "Z" * 5
    # Act
    try:
        _run(gt._extract_token(_Page("u", js_value=partial)))
        message = ""
    except gt.GitHubTokenFlowError as exc:
        message = str(exc)
    # Assert
    assert partial not in message


def test_sync_entry_requires_permissions():
    # Arrange
    kwargs = dict(permissions={}, on_token=lambda v: None, user_data_dir="/x")
    # Act
    call = lambda: gt.github_create_fine_grained_token("n", "o", **kwargs)  # noqa: E731
    # Assert
    with pytest.raises(ValueError):
        call()
