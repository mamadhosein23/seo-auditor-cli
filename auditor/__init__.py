"""Command-line interface for SEO and web performance auditing.

Provides tools to analyze web performance, evaluate on-page SEO factors,
and validate site endpoints.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Final

# Must match the distribution name declared in the project metadata.
_DISTRIBUTION_NAME: Final[str] = "auditor"
_FALLBACK_VERSION: Final[str] = "0.0.0.dev0"

try:
    __version__: Final[str] = version(_DISTRIBUTION_NAME)
except PackageNotFoundError:
    __version__: Final[str] = _FALLBACK_VERSION

__all__: Final[tuple[str, ...]] = ("__version__",)

# Standard module attributes exposed for introspection and interactive tools.
_MODULE_ATTRS: Final[frozenset[str]] = frozenset(
    {
        "__annotations__",
        "__builtins__",
        "__cached__",
        "__doc__",
        "__file__",
        "__loader__",
        "__name__",
        "__package__",
        "__path__",
        "__spec__",
    }
)


def __dir__() -> list[str]:
    """Return public exports and standard module attributes."""
    return sorted(set(__all__) | (_MODULE_ATTRS & globals().keys()))
