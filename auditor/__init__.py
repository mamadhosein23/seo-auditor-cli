"""Command-line interface for SEO and web performance auditing.

Provides tools to analyze web performance, evaluate on-page SEO factors,
and validate site endpoints.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Final

# This must match the project distribution name in pyproject.toml.
_DISTRIBUTION_NAME: Final = "auditor"
_FALLBACK_VERSION: Final = "0.0.0.dev0"

try:
    _version = version(_DISTRIBUTION_NAME)
except PackageNotFoundError:
    _version = _FALLBACK_VERSION

__version__: Final[str] = _version
__all__: Final[tuple[str, ...]] = ("__version__",)

# Standard module attributes recognized by introspection tools.
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
    """Return the module's public exports and standard runtime attributes."""
    return sorted(set(__all__) | (_MODULE_ATTRS & globals().keys()))
