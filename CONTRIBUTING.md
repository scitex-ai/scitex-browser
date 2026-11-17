# Contributing to SciTeX

Thank you for your interest in contributing to SciTeX. This guide covers the
process for reporting issues, suggesting features, and submitting code.

## Contributor License Agreement

Before your first contribution can be merged, you must agree to the
[SciTeX CLA](CLA.md). This is a one-time process. The CLA ensures that:

- You retain copyright of your work.
- The project can continue to offer dual licensing (free for researchers,
  commercial for enterprises).

See [CLA.md](CLA.md) for full details.

## Reporting Issues

- Search [existing issues](https://github.com/ywatanabe1989/scitex-browser/issues)
  before opening a new one.
- Include a minimal reproducible example when reporting bugs.
- Specify your Python version, OS, and `scitex` version.

## Development Setup

```bash
git clone git@github.com:ywatanabe1989/scitex-browser.git
cd scitex-browser
pip install -e ".[dev]"
```

## Branch Workflow

- `main` — stable releases only. Do not push directly.
- `develop` — integration branch. PRs target here.
- Feature branches — create from `develop`, name as `feature/<description>`.

```bash
git checkout develop
git checkout -b feature/my-change
# ... make changes ...
git push origin feature/my-change
# Open PR targeting develop
```

## Code Style

- Follow existing conventions in the codebase.
- Use `_` prefix for internal/private modules and functions.
- Keep files under 512 lines.
- Run tests before submitting:

```bash
pytest tests/ -x -q
```

## Pull Request Process

1. Ensure your branch is up to date with `develop`.
2. Write tests for new functionality.
3. Run the test suite and confirm all tests pass.
4. Open a PR targeting `develop` with a clear description.
5. The CLA bot will check your CLA status on your first PR.

## License

By contributing, you agree to the terms of the [CLA](CLA.md), which includes
licensing under AGPL-3.0 (see [LICENSE](LICENSE)) and the dual-licensing
provisions described therein.


## Release artifact verification

Release helpers require Python 3.11 or newer, as supplied by the release SIF.
The build records source identity, generated metadata and archive hashes in
dist/release-proof.json. The publisher recomputes that proof before requesting
OIDC credentials, and uploads only the wheel and sdist to PyPI.

The archive algorithms come from the fixed shared release core at
12f0e6bd5654bd89dd82165d5fe5aa0a9d9b0607. Every module is checked against its
recorded SHA256 before execution. Artifacts that differ from the selected Git
source, expected version or recorded proof refuse, as do unexpected dist members. The proof grants no tag, native
runtime or publication authority: protected-main source, qualified release
profiles and actual PyPI publisher registration remain separate requirements.

Private qualification of an already public version must never be uploaded.


Before either PyPI minting or GitHub Release creation, the shared SIF gate also
revalidates the actual remote tag, its metadata/version and protected-main
ancestry. It reads main before and after qualification and rereads the original
tag object; movement or disagreement with the recorded build stops the release.
These GitHub requests reuse the job's existing scoped token at the relevant
step, without changing job permissions. Read-only source verification does not
establish actor admission, native runtime qualification or PyPI publisher trust.

## Browser image qualification

The generic CI images do not include Chromium's native dependencies. The
Browser-owned candidate recipe at .github/ci/ci-browser.def layers a pinned
Playwright installer, matching Chromium and its system libraries on a separately
qualified base SIF. Set BASE_SIF to that image's absolute path and BASE_SHA256 to
its independently recorded digest, then build a new output image:

```bash
apptainer build --build-arg base_image="$BASE_SIF" \
  --build-arg base_sha256="$BASE_SHA256" \
  ci-browser.sif .github/ci/ci-browser.def
```

The recipe verifies the base digest and runs an actual browser launch/page check.
Its dedicated tooling environment leaves the base Python environments intact.
It uses container scratch for that check, rather than inheriting a host-only
temporary directory.

After building source-bound wheel/sdist archives, select the candidate through
SCITEX_CI_SIF and its recorded SCITEX_CI_SIF_SHA256. With the existing writable
RUNNER_TEMP and SCITEX_BROWSER_RELEASE_SOURCE_SHA/VERSION expectations set, run:

```bash
bash .github/ci/exec-in-sif.sh probe-wheel-in-sif.sh 3.12
```

This verifies the artifact proof, creates a fresh environment, installs the wheel
with normal base dependencies, checks dependency consistency, and runs the real
offline fill/value/events/missing-selector probe using Chromium inside the image.
It clears source PYTHONPATH and removes only its own fresh installation afterward.
No host browser, saved profile, live website or application login is required.

The pinned shared native Browser executor requires this helper after its
complete artifact build and before upload. The leaf release caller resolves the
tag, trigger and protected-main source on a hosted runner; native test/build
operations receive that same source and tag without inheriting secrets.
Publisher and GitHub Release jobs download the matching source-named artifact
and retain their final archive and remote-source checks. Actual publisher trust
and the remaining release requirements must be verified before publishing.
