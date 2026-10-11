"""SEO and performance auditing command-line interface.

Provides tools to analyze web performance metrics, evaluate on-page SEO
factors, and validate site endpoints.
"""

from importlib.metadata import PackageNotFoundError, version

# نام دقیق پکیج در pyproject.toml تحت [project.name]
DISTRIBUTION_NAME: str = "auditor"

try:
    __version__: str = version(DISTRIBUTION_NAME)
except PackageNotFoundError:
    # پکیج در حالت محلی اجرا شده و هنوز install نشده است
    __version__ = "0.0.0.dev0"

__all__: list[str] = ["__version__"]
