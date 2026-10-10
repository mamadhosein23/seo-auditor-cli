"""SEO and performance auditing command-line interface.

Provides tools to analyze web performance metrics, evaluate on-page SEO
factors, and validate site endpoints.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("auditor")
except PackageNotFoundError:
    # Fallback to development version if the package is not installed/editable
    __version__ = "0.1.0.dev0"

__all__ = ["__version__"]
