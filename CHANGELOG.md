# Changelog

All notable changes to `scitex-browser` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
