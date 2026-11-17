#!/usr/bin/env bash
# Qualification helper inside a verified Browser image; no release admission.
set -euo pipefail
V="${1:-3.12}"
PY="/opt/venv-$V/bin/python"
TOOLS=/opt/browser-tools/bin/python
test -x "$PY" && test -x "$TOOLS" || {
    echo "::error::Browser image tooling is required" >&2
    exit 1
}
: "${SCITEX_BROWSER_RELEASE_SOURCE_SHA:?tested build source is required}"
: "${SCITEX_BROWSER_RELEASE_VERSION:?tested release version is required}"
"$PY" -I -S -B .github/ci/release-identity.py verify-proof \
    --commit "$SCITEX_BROWSER_RELEASE_SOURCE_SHA" \
    --version "${SCITEX_BROWSER_RELEASE_VERSION#v}" --dist dist

ROOT="$(mktemp -d /tmp/scitex-browser-wheel.XXXXXXXX)"
trap 'rm -rf -- "$ROOT"' EXIT
export UV_CACHE_DIR="$ROOT/uv-cache"
export PIP_CACHE_DIR="$ROOT/pip-cache"
export PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
unset VIRTUAL_ENV PYTHONPATH
uv venv --python "$PY" "$ROOT/venv"
# The proof above requires exactly one wheel; install its normal base deps.
uv pip install --python "$ROOT/venv/bin/python" dist/*.whl
uv pip check --python "$ROOT/venv/bin/python"
BROWSER="$("$TOOLS" -I -c 'from playwright.sync_api import sync_playwright; p=sync_playwright().start(); print(p.chromium.executable_path); p.stop()')"
"$ROOT/venv/bin/python" -I .github/ci/probe-interactions.py --executable "$BROWSER"
