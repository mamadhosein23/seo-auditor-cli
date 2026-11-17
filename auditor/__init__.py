"""Command-line interface and library for SEO and web performance auditing.

Provides tools to analyze web performance metrics, evaluate on-page SEO
factors, and validate site endpoints.
"""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Final

# Distribution name registered in pyproject.toml [project.name]
_DISTRIBUTION_NAME: Final[str] = "auditor"

# Fallback version used in local, editable, or non-installed source checkouts
_FALLBACK_VERSION: Final[str] = "0.0.0.dev0"


def _get_version(dist_name: str, fallback: str) -> str:
    """Retrieve the installed package version safely.

    Parameters
    ----------
    dist_name : str
        The package distribution name as registered in package metadata.
    fallback : str
        The fallback version string to return if metadata is unavailable.

    Returns
    -------
    str
        The resolved semantic version string.
    """
    try:
        return version(dist_name)
    except PackageNotFoundError:
        return fallback


# Public version constant exposed at package root
__version__: Final[str] = _get_version(_DISTRIBUTION_NAME, _FALLBACK_VERSION)

# Explicit public API export contract (PEP 484 & typing guidelines)
__all__: Final[tuple[str, ...]] = ("__version__",)

# Standard module-level dunder attributes per PEP 562 and CPython runtime specs
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
    """Expose explicit public exports merged with standard module dunders.

    Implements PEP 562 dynamic attribute inspection to hide internal helpers
    and constants from interactive autocompletion and dir() scans.

    Returns
    -------
    list[str]
        Sorted list of exposed attribute names.
    """
    current_globals = globals()
    active_dunders = {attr for attr in _MODULE_ATTRS if attr in current_globals}
    return sorted(set(__all__) | active_dunders)


def __getattr__(name: str) -> object:
    """Safely catch unexported access and raise a clear AttributeError (PEP 562).

    Parameters
    ----------
    name : str
        The name of the attribute attempted to be accessed.

    Raises
    ------
    AttributeError
        Raised whenever an undefined or private module attribute is requested.
    """
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}. "
        f"Available public exports: {', '.join(__all__)}"
    )
