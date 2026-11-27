"""Reusable, human-in-the-loop-safe browser flows on dedicated profiles."""

from ._dedicated_profile import (
    DedicatedChrome,
    DedicatedProfileError,
    attach_dedicated_chrome,
    attached_page,
    launch_dedicated_chrome,
)
from .github_tokens import (
    GitHubAuthPromptError,
    GitHubTokenFlowError,
    github_approve_token_request_async,
    github_create_fine_grained_token,
    github_create_fine_grained_token_async,
    normalize_permissions,
)

__all__ = [
    "DedicatedChrome",
    "DedicatedProfileError",
    "attach_dedicated_chrome",
    "attached_page",
    "launch_dedicated_chrome",
    "GitHubAuthPromptError",
    "GitHubTokenFlowError",
    "github_approve_token_request_async",
    "github_create_fine_grained_token",
    "github_create_fine_grained_token_async",
    "normalize_permissions",
]
