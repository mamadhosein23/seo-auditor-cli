from typing import Any
import pytest
from auditor.engine import validate_url


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "http://example.com/page?id=1",
        "https://sub.example.com:8443/path",
        "https://example.com/search?q=test#section",
        "https://xn--bcher-kva.example",  # IDN / Punycode
        "http://[::1]:8080/path",          # IPv6
    ],
)
def test_accepts_valid_http_urls(url: str) -> None:
    assert validate_url(url) == url


@pytest.mark.parametrize(
    ("url", "error_pattern"),
    [
        ("", r"empty url"),
        ("   ", r"empty url"),
        ("example.com", r"invalid scheme"),
        ("ftp://example.com", r"unsupported scheme"),
        ("javascript:alert(1)", r"unsupported scheme"),
        ("https://", r"missing host"),
        ("https:///", r"missing host"),
        ("https://example.com:invalid", r"invalid port"),
        ("https://example.com:70000", r"port out of range"),
        ("https://:8080", r"missing host"),
    ],
)
def test_rejects_invalid_urls(url: str, error_pattern: str) -> None:
    # پیام خطای دقیق مانع از pass شدن اشتباهی تست توسط استثناهای پیش‌بینی‌نشده می‌شود
    with pytest.raises(ValueError, match=rf"(?i){error_pattern}"):
        validate_url(url)


@pytest.mark.parametrize(
    "invalid_input",
    [None, 123, 3.14, [], {}, b"https://example.com"],
)
def test_rejects_non_string_types(invalid_input: Any) -> None:
    with pytest.raises(TypeError, match=r"(?i)expected str"):
        validate_url(invalid_input)
