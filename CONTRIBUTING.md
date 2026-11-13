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
