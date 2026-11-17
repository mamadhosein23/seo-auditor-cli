"""Command-line tools for SEO and web performance auditing.

Analyze web performance, evaluate on-page SEO factors, and validate
site endpoints.
"""

from importlib.metadata import PackageNotFoundError, version
from typing import Final

# Keep this in sync with the project name in pyproject.toml.
_DISTRIBUTION_NAME: Final[str] = "auditor"
_FALLBACK_VERSION: Final[str] = "0.0.0.dev0"


def _resolve_version() -> str:
    """Return the installed distribution version, or a development fallback."""
    try:
        return version(_DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return _FALLBACK_VERSION


__version__: Final[str] = _resolve_version()

__all__: Final[tuple[str, ...]] = ("__version__",)
