"""SEO and performance auditing command-line interface.

Provides tools to analyze web performance metrics, evaluate on-page SEO
factors, and validate site endpoints.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Final

# Distribution identifier registered in pyproject.toml
_DISTRIBUTION_NAME: Final[str] = "auditor"
_FALLBACK_VERSION: Final[str] = "0.0.0.dev0"

try:
    _installed_version = version(_DISTRIBUTION_NAME)
except PackageNotFoundError:
    _installed_version = _FALLBACK_VERSION

__version__: Final[str] = _installed_version

__all__: Final[tuple[str, ...]] = ("__version__",)

# Standard dunder attributes expected by runtime introspection, IDEs, and REPLs
_MODULE_ATTRS: Final[frozenset[str]] = frozenset({
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
})


def __dir__() -> list[str]:
    """Return explicit public exports combined with runtime module dunders (PEP 562)."""
    return sorted(set(__all__) | (_MODULE_ATTRS & globals().keys()))
