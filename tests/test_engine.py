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
    # اگر تابع ورودی را برمی‌گرداند مقدار را با خودش بسنجید؛ اگر چیزی برنمی‌گرداند از assert validate_url(url) is None استفاده کنید
    assert validate_url(url) == url


@pytest.mark.parametrize(
    ("url", "error_pattern"),
    [
        ("", "cannot be empty"),
        (" example.com ", "invalid"),
        ("example.com", "missing scheme"),
        ("ftp://example.com", "unsupported scheme"),
        ("https://", "missing host"),
        ("https://example.com:invalid", "invalid port"),
        ("https://example.com:70000", "port out of range"),
        ("javascript:alert(1)", "unsupported scheme"),
    ],
)
def test_rejects_invalid_urls(url: str, error_pattern: str) -> None:
    with pytest.raises(ValueError, match=error_pattern):
        validate_url(url)


@pytest.mark.parametrize("invalid_input", [None, 123, [], {}])
def test_rejects_non_string_types(invalid_input: object) -> None:
    with pytest.raises(TypeError):
        validate_url(invalid_input)  # type: ignore[arg-type]
