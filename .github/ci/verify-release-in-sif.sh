#!/usr/bin/env bash
# Run inside the qualified SIF before either publication boundary.
set -euo pipefail
V="${1:-3.12}"
PY="/opt/venv-$V/bin/python"
test -x "$PY" || { echo "::error::missing release interpreter: $PY"; exit 1; }
: "${SCITEX_BROWSER_RELEASE_SOURCE_SHA:?tested build source is required}"
: "${SCITEX_BROWSER_RELEASE_VERSION:?tested release version is required}"
"$PY" -I -S -B .github/ci/release-identity.py verify-proof \
    --commit "$SCITEX_BROWSER_RELEASE_SOURCE_SHA" \
    --version "${SCITEX_BROWSER_RELEASE_VERSION#v}" --dist dist
"$PY" -I -S -B .github/ci/release-source.py \
    --tag "v${SCITEX_BROWSER_RELEASE_VERSION#v}" \
    --commit "$SCITEX_BROWSER_RELEASE_SOURCE_SHA"
