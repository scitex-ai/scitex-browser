# Changelog

All notable changes to `scitex-browser` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.17] - 2026-11-27

First PyPI release since 0.1.15. `v0.1.16` was tagged but never published to
PyPI: its tag-triggered release workflow failed in the test job before build,
because `.github/ci/exec-in-sif.sh` hardcoded Spartan HPC paths
(`/data/gpfs/projects/punim0264/...`) that do not exist on the current runners.
0.1.17 ships everything listed under 0.1.16 below.

### Changed
- Release CI: ported scitex-clew's tag-driven release pipeline and its
  `.github/ci` scripts (Postgres-specific parts removed). Tag tests run natively
  under uv with job-owned state (`native-job.sh`); build and publish run in the
  digest-verified CI SIF (`exec-in-sif.sh`) with no host-specific paths; the
  build checks that the tag owns the commit and that wheel/sdist/installed
  metadata match `pyproject.toml` (`check-dist.py`) before OIDC trusted
  publishing (`publish-oidc.py`).
- Removed the Spartan-specific `run-in-sif.sh` test entry point.

## [0.1.16] - 2026-11-27

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
