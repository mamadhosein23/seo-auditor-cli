"""SEO and performance auditing command-line interface.

Provides tools to analyze web performance metrics, evaluate on-page SEO
factors, and validate site endpoints.
"""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final

# Distribution identifier registered in pyproject.toml
_DISTRIBUTION_NAME: Final[str] = "auditor"
_FALLBACK_VERSION: Final[str] = "0.0.0.dev0"

try:
    __version__: Final[str] = version(_DISTRIBUTION_NAME)
except PackageNotFoundError:
    # Triggered during uninstalled local execution or non-editable developer checkouts
    __version__ = _FALLBACK_VERSION

__all__: Final[tuple[str, ...]] = ("__version__",)


def __dir__() -> list[str]:
    """Expose only public symbols explicitly declared in __all__."""
    return sorted(__all__)
