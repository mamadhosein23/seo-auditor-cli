from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from functools import cache
from typing import Final

# تنظیمات ثابت در سطحی بالاتر از کد
_DISTRIBUTION_NAME: Final = "auditor"
_FALLBACK_VERSION: Final = "0.0.0.dev0"

@cache
def __get_version() -> str:
    """Resolve the distribution version with internal memoization."""
    try:
        return version(_DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return _FALLBACK_VERSION

# تزریق مستقیم نسخه به __version__
__version__: Final = __get_version()

# کنترل دقیق بر API عمومی (مینیمالیسم در بهترین حالت)
__all__: Final = ("__version__",)
