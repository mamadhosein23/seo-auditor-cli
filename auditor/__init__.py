"""Command-line tools for SEO and web performance auditing.

Analyze web performance, evaluate on-page SEO factors, and validate
site endpoints.
"""

from importlib.metadata import PackageNotFoundError, version
from typing import Final

# Must match the distribution name in pyproject.toml.
_DISTRIBUTION_NAME: Final = "auditor"

try:
    __version__: Final[str] = version(_DISTRIBUTION_NAME)
except PackageNotFoundError:
    __version__: Final[str] = "0.0.0.dev0"

__all__ = ("__version__",)
