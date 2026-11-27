#!/usr/bin/env bash
# Source inside the verified SIF or a native job. Only the outer wrapper chooses job state.
# Ported from scitex-clew's .github/ci (Postgres-specific isolation removed).
set -euo pipefail
: "${BROWSER_CI_STATE:?job-owned state must be supplied by exec-in-sif.sh or native-job.sh}"
[[ "$BROWSER_CI_STATE" = /* ]] || { echo '::error::job state must be absolute'; exit 1; }
umask 077
mkdir -p "$BROWSER_CI_STATE"/{scitex,config,data,cache,tmp,site,installed}
mkdir -p "$BROWSER_CI_STATE/gnupg"
export TMPDIR="$BROWSER_CI_STATE/tmp" SCITEX_DIR="$BROWSER_CI_STATE/scitex"
export XDG_CONFIG_HOME="$BROWSER_CI_STATE/config" XDG_DATA_HOME="$BROWSER_CI_STATE/data"
export XDG_CACHE_HOME="$BROWSER_CI_STATE/cache" XDG_STATE_HOME="$BROWSER_CI_STATE"
export XDG_RUNTIME_DIR="$BROWSER_CI_STATE/tmp" GNUPGHOME="$BROWSER_CI_STATE/gnupg"
export PIP_CACHE_DIR="$BROWSER_CI_STATE/cache/pip" UV_CACHE_DIR="$BROWSER_CI_STATE/cache/uv"
export PIP_CONFIG_FILE=/dev/null PIP_INDEX_URL=https://pypi.org/simple
export UV_NO_CONFIG=1 PIP_NO_INPUT=1
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
export NETRC="$BROWSER_CI_STATE/netrc"
: > "$NETRC"
printf '{}\n' > "$BROWSER_CI_STATE/config.yaml"
export SCITEX_CONFIG_PATH="$BROWSER_CI_STATE/config.yaml"
export NPM_CONFIG_USERCONFIG="$BROWSER_CI_STATE/npm-user.conf"
export NPM_CONFIG_GLOBALCONFIG="$BROWSER_CI_STATE/npm-global.conf"
export NPM_CONFIG_CACHE="$BROWSER_CI_STATE/cache/npm"
: > "$NPM_CONFIG_USERCONFIG"; : > "$NPM_CONFIG_GLOBALCONFIG"
export MPLBACKEND=Agg MPLCONFIGDIR="$BROWSER_CI_STATE/matplotlib"
mkdir -p "$MPLCONFIGDIR"
unset VIRTUAL_ENV
