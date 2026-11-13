# Changelog

All notable changes to `scitex-browser` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

- Bind release tests, builds and publisher scripts to the same tagged commit
  on main, and reject malformed or mismatched manual release selections.
- Keep CLA automation on an explicit hosted runner with its one required secret.
- Fail cross-package import checks for missing submodules of installed peers;
  keep absent optional peers as visible skips.
- Declare Matplotlib and pytest as runtime dependencies for the packaged
  plotting entrypoints and pytest fixture factories.
- Use SciTeX console/logging channels for browser feedback, preserve explicit
  verbose/debug feedback on stdout/stderr, and silence import-only status.
- Run the skills-quality gate against the package root instead of skipping it.
- Require the installed Python auditor even when its CLI is absent from PATH.
- Verify release SIF digests and use job-owned portable scratch/binds.
- Pass selector and value as one Playwright evaluate argument so JavaScript
  fill sets the value and emits input/change events.
- Correct interaction examples to use scalar CSS selectors, viewport-center
  clicks and explicit popup methods; align README fallback and artifact details.

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
