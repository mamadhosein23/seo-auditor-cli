from __future__ import annotations

from urllib.parse import urlsplit


_ALLOWED_SCHEMES = {"http", "https"}


def validate_url(url: str) -> str:
    """Validate an absolute HTTP(S) URL and return it unchanged.

    Raises:
        TypeError: If `url` is not a string.
        ValueError: If it is empty, contains whitespace, or is not a valid
            absolute HTTP(S) URL with a host.
    """
    if not isinstance(url, str):
        raise TypeError("URL must be a string")

    if not url:
        raise ValueError("URL cannot be empty")

    if any(char.isspace() for char in url):
        raise ValueError("URL cannot contain whitespace")

    try:
        parsed = urlsplit(url)
    except ValueError as exc:
        # For example, malformed IPv6 addresses can fail during parsing.
        raise ValueError(f"Invalid URL: {exc}") from exc

    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise ValueError("URL scheme must be http or https")

    if not parsed.netloc or not parsed.hostname:
        raise ValueError("URL must include a host")

    # Accessing .port validates that a supplied port is numeric and in range.
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError(f"Invalid URL port: {exc}") from exc

    return url
