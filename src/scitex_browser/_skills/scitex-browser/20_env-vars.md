---
description: |
  [TOPIC] Env Vars
  [DETAILS] Environment variables read by scitex-browser at import / runtime. Follow SCITEX_<MODULE>_* convention — see general/10_arch-environment-variables.md.
tags: [scitex-browser-env-vars]
---

# scitex-browser — Environment Variables

| Variable | Purpose | Default | Type |
|---|---|---|---|
| `SCITEX_BROWSER_CHROME_CACHE_DIR` | Override for the Chromium user-data dir used by Playwright sessions. | `$SCITEX_DIR/browser/runtime/chrome` | path |

## Cross-package vars (read by scitex-browser but owned elsewhere)

scitex-browser also consumes credentials/config owned by other packages for
authenticated sessions (scholar paywall access, cloud login). These must be
set by the respective upstream package; scitex-browser reads them read-only:

| Variable | Owner | Purpose |
|---|---|---|
| `SCITEX_CLOUD_USERNAME` | scitex-cloud | SSO login for cloud sessions |
| `SCITEX_CLOUD_PASSWORD` | scitex-cloud | SSO password for cloud sessions |
| `SCITEX_SCHOLAR_OPENURL_RESOLVER_URL` | scitex-scholar | Institutional OpenURL resolver |
| `SCITEX_SCHOLAR_2CAPTCHA_API_KEY` | scitex-scholar | CAPTCHA-solving API key for paywall traversal |
| `SCITEX_SCHOLAR_ZENROWS_API_KEY` | scitex-scholar | ZenRows anti-bot proxy API key |
| `SCITEX_SCHOLAR_ZENROWS_PROXY_COUNTRY` | scitex-scholar | ZenRows geo override |
| `SCITEX_DIR` | ecosystem | Base SciTeX data directory |

## Feature flags

None. All vars are configuration values, not flags.

## Audit

```bash
grep -rhoE 'SCITEX_[A-Z0-9_]+' $HOME/proj/scitex-browser/src/ | sort -u
```
