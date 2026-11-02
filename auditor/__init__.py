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


def __dir__() -> list[str]:
    """Expose public symbols declared in __all__ along with standard module attributes."""
    # تضمین حفظ اتریبیوت‌های سیستمی ماژول برای سازگاری کامل با IDEها و REPL
    return sorted(set(globals().keys()) | set(__all__))
