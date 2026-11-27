#!/usr/bin/env bash
# Native installer/application context; ambient provider identities stay outside it.
# Ported from scitex-clew's .github/ci (Postgres service-test mode removed).
set -euo pipefail
: "${RUNNER_TEMP:?job-owned temporary directory required}"
[[ "$#" -gt 0 ]] || { echo '::error::native job command required'; exit 1; }
if [[ -z "${BROWSER_CI_STATE-}" ]]; then
  BROWSER_CI_STATE="$(mktemp -d "$RUNNER_TEMP/browser-native.XXXXXX")"
  export BROWSER_CI_STATE
  if [[ -n "${GITHUB_ENV-}" ]]; then
    printf 'BROWSER_CI_STATE=%s\n' "$BROWSER_CI_STATE" >> "$GITHUB_ENV"
  fi
fi
source .github/ci/job-state.sh
# Native file permission assertions require the documented ordinary umask.
umask 022
export UV_PYTHON_INSTALL_DIR="$BROWSER_CI_STATE/uv-python"
context=(
  "PATH=${PATH:?}" "LANG=C.UTF-8" "LC_ALL=C.UTF-8"
  "BROWSER_CI_STATE=$BROWSER_CI_STATE" "RUNNER_TEMP=$RUNNER_TEMP"
  "SCITEX_DIR=$SCITEX_DIR" "SCITEX_CONFIG_PATH=$SCITEX_CONFIG_PATH"
  "TMPDIR=$TMPDIR" "XDG_CONFIG_HOME=$XDG_CONFIG_HOME" "XDG_CACHE_HOME=$XDG_CACHE_HOME"
  "XDG_DATA_HOME=$XDG_DATA_HOME" "XDG_STATE_HOME=$XDG_STATE_HOME" "XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"
  "GNUPGHOME=$GNUPGHOME" "NETRC=$NETRC"
  "PIP_CONFIG_FILE=$PIP_CONFIG_FILE" "PIP_INDEX_URL=$PIP_INDEX_URL"
  "PIP_CACHE_DIR=$PIP_CACHE_DIR" "PIP_NO_INPUT=$PIP_NO_INPUT"
  "UV_CACHE_DIR=$UV_CACHE_DIR" "UV_NO_CONFIG=$UV_NO_CONFIG" "UV_PYTHON_INSTALL_DIR=$UV_PYTHON_INSTALL_DIR"
  "PYTHON_KEYRING_BACKEND=$PYTHON_KEYRING_BACKEND"
  "NPM_CONFIG_USERCONFIG=$NPM_CONFIG_USERCONFIG" "NPM_CONFIG_GLOBALCONFIG=$NPM_CONFIG_GLOBALCONFIG"
  "NPM_CONFIG_CACHE=$NPM_CONFIG_CACHE"
  "MPLBACKEND=$MPLBACKEND" "MPLCONFIGDIR=$MPLCONFIGDIR"
)
# Preserve the actual native HOME value; it never chooses job-owned state.
if [[ -v HOME ]]; then context+=("HOME=$HOME"); fi
exec env -i "${context[@]}" "$@"
