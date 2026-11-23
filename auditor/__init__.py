from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Final

# Constants at the top level
_DISTRIBUTION_NAME: Final[str] = "auditor"
_FALLBACK_VERSION: Final[str] = "0.0.0.dev0"

def _get_version() -> str:
    """Resolve the distribution version safely."""
    try:
        return version(_DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return _FALLBACK_VERSION

# Set the public version
__version__: Final[str] = _get_version()

# Explicit public API definition
__all__: Final[tuple[str, ...]] = ("__version__",)
