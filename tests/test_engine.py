import pytest
from auditor.engine import validate_url


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "http://example.com/page?id=1",
        "https://sub.example.com:8443/path",
        "https://example.com/search?q=test#section",
    ],
)
def test_accepts_valid_http_urls(url: str) -> None:
    # Ensure the function returns the URL as-is or sanitized
    assert validate_url(url) == url


@pytest.mark.parametrize(
    ("url", "error_pattern"),
    [
        ("", r"(?i)empty"),
        (" example.com ", r"(?i)(invalid|scheme)"),
        ("example.com", r"(?i)scheme"),
        ("ftp://example.com", r"(?i)scheme"),
        ("https://", r"(?i)(host|netloc)"),
        ("https://example.com:invalid", r"(?i)port"),
        ("https://example.com:70000", r"(?i)port"),
        ("javascript:alert(1)", r"(?i)scheme"),
    ],
)
def test_rejects_invalid_urls(url: str, error_pattern: str) -> None:
    # Use regex pattern to match error message without tight coupling
    with pytest.raises(ValueError, match=error_pattern):
        validate_url(url)


@pytest.mark.parametrize("invalid_input", [None, 123, [], {}, b"https://example.com"])
def test_rejects_non_string_types(invalid_input: object) -> None:
    # Ensure strict type checking for inputs
    with pytest.raises(TypeError):
        validate_url(invalid_input)  # type: ignore[arg-type]
