# Changelog

All notable changes to `scitex-browser` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- Configure subprocess coverage via coverage.py `patch = ["subprocess"]` instead of installing a `.pth` hook into site-packages or overwriting `COVERAGE_PROCESS_START` / `COVERAGE_FILE` at test collection time.

### Added
- `scitex_browser.flows`: `launch_dedicated_chrome` / `attach_dedicated_chrome` /
  `attached_page` for a dedicated signed-in profile with loopback DevTools
  (native and WSL to Windows Chrome), tab-safe and close-only-what-we-launched.
- `github_create_fine_grained_token` (+ async form): fills, reads back and
  submits GitHub's fine-grained PAT form, hands the value only to a callback,
  and raises on any sign-in, sudo or 2FA prompt. Also
  `github_approve_token_request_async` and `github_delete_fine_grained_token_async`.
- Rendered HTML/text capture through `fetch_content`, `get_text`, `get_html`,
  `save_as_html`, and `save_as_text`, with matching async functions.
- Chat thread extraction through an existing CDP browser session, with
  transcript formatting and explicit extraction errors.

## [0.1.15]

### Added
- `scitex_browser.debugging.capture_debug_artifacts_async(page, label=...)` —
  always-on screenshot + HTML capture at any interaction so post-mortem of
  selector regressions is mechanical. This is the helper consumers import to
  satisfy the PA-305 browser-automation-debugging rule.

### Changed
- Route all package runtime writes under `~/.scitex/browser/runtime/`.

### Tests
- Drop playwright/`unittest.mock` mocks in favor of hand-rolled fakes and
  real-collaborator tests; satisfy PA-306 (no-mocks) and PA-307 (test-quality).

## [0.1.14]

- Initial CHANGELOG entry — see git log for prior history.
