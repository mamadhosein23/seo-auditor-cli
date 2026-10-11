"""SEO and performance auditing command-line interface.

Provides tools to analyze web performance metrics, evaluate on-page SEO
factors, and validate site endpoints.
"""

from importlib.metadata import PackageNotFoundError, version

# Must match the distribution name defined in pyproject.toml [project.name]
DISTRIBUTION_NAME: str = "auditor"

try:
    __version__: str = version(DISTRIBUTION_NAME)
except PackageNotFoundError:
    # Fallback version for local development runs without installation
    __version__ = "0.0.0.dev0"

__all__: list[str] = ["__version__"]
