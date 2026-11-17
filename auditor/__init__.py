"""Public package interface for the Auditor project.

Auditor provides command-line and programmatic tools for analyzing web
performance, evaluating on-page SEO, and validating website endpoints.

The package version is resolved from the installed distribution metadata.
When the metadata is unavailable, such as in an unpackaged source checkout,
a PEP 440-compatible development version is used as a fallback.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as distribution_version
from typing import Final

# This value must match the `project.name` field in `pyproject.toml`.
_DISTRIBUTION_NAME: Final[str] = "auditor"

# PEP 440-compatible version used when distribution metadata is unavailable.
_FALLBACK_VERSION: Final[str] = "0.0.0.dev0"


def _resolve_version(
    distribution_name: str = _DISTRIBUTION_NAME,
    fallback: str = _FALLBACK_VERSION,
) -> str:
    """Resolve the installed distribution version.

    Args:
        distribution_name:
            Distribution name registered in the package metadata.
        fallback:
            Version returned when the distribution metadata cannot be found.

    Returns:
        The installed distribution version, or the provided fallback.

    Notes:
        Only ``PackageNotFoundError`` is handled intentionally. Other metadata
        errors are allowed to propagate because they may indicate a broken
        installation that should not be silently ignored.
    """
    if not distribution_name:
        raise ValueError("Distribution name must not be empty.")

    if not fallback:
        raise ValueError("Fallback version must not be empty.")

    try:
        return distribution_version(distribution_name)
    except PackageNotFoundError:
        return fallback


__version__: Final[str] = _resolve_version()

# Define the package's supported public API explicitly.
__all__: Final[tuple[str, ...]] = ("__version__",)
