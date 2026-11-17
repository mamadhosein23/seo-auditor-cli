"""Command-line tools for SEO and web performance auditing.

Analyze web performance, inspect on-page SEO factors, and validate
site endpoints.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Final

# The distribution name declared in the project's package metadata.
_DISTRIBUTION_NAME: Final[str] = "auditor"

# Used when the package metadata is unavailable, such as in a source checkout.
_FALLBACK_VERSION: Final[str] = "0.0.0.dev0"


def _get_version() -> str:
    """Return the installed package version or a development fallback."""
    try:
        return version(_DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return _FALLBACK_VERSION


__version__: Final[str] = _get_version()

# Names intentionally exported by this module.
__all__: Final[tuple[str, ...]] = ("__version__",)

# Standard module attributes useful to introspection tools and interactive shells.
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
    """List public exports and standard attributes currently defined in the module."""
    available_attrs = _MODULE_ATTRS.intersection(globals())
    return sorted((*__all__, *available_attrs))
