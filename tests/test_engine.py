from __future__ import annotations

import re
from typing import Final

import pytest

# فرض: استثنای استاندارد اعتبارسنجی
from auditor.engine import ValidationError, validate_url

# ---------------------------------------------------------------------------
# FIXTURES & CONSTANTS
# ---------------------------------------------------------------------------
MAX_URL_LENGTH_OCTETS: Final[int] = 2048


# ---------------------------------------------------------------------------
# POSITIVE TEST CASES (RFC 3986 & WHATWG Standards)
# ---------------------------------------------------------------------------
class TestValidateUrlSuccess:
    """تست پذیرش URLهای معتبر مطابق با استانداردهای رسمی شبکه."""

    @pytest.mark.parametrize(
        "url",
        [
            # استانداردهای پایه
            pytest.param("https://example.com", id="standard_https"),
            pytest.param("http://example.com/page?id=1&category=test", id="query_params"),
            pytest.param("https://sub.domain.example.com:8443/path/to/res", id="custom_port"),
            pytest.param("https://example.com/#overview", id="fragment_only"),
            pytest.param("https://example.com/search?q=foo#bar", id="query_and_fragment"),
            
            # کاراکترهای بین‌المللی (Punycode / IDN)
            pytest.param("https://xn--bcher-kva.example", id="punycode_idn"),
            
            # آدرس‌های معتبر شبکه
            pytest.param("http://127.0.0.1:3000/api/v1", id="ipv4_loopback"),
            pytest.param("http://[::1]:8080/metrics", id="ipv6_loopback"),
            pytest.param("http://[2001:db8::ff00:42:8329]:80/", id="ipv6_full_address"),
            
            # احراز هویت مجاز
            pytest.param("https://auditor_agent:super-secret@example.com/jobs", id="basic_auth_valid"),
        ],
    )
    def test_accepts_valid_urls(self, url: str) -> None:
        """بررسی ثبات نوع (Type Invariance) و برابری نگاشت خروجی."""
        validated: str = validate_url(url)
        assert validated == url
        assert isinstance(validated, str)


# ---------------------------------------------------------------------------
# NEGATIVE TEST CASES (Security, Exploits & Malformed inputs)
# ---------------------------------------------------------------------------
class TestValidateUrlFailures:
    """تست رد انواع داده‌های خراب، پروتکل‌های ممنوع و بردارهای نفوذ SSRF."""

    @pytest.mark.parametrize(
        ("url", "err_regex"),
        [
            # خالی یا کاراکترهای کنترلی
            pytest.param("", r"(?i)empty", id="empty_string"),
            pytest.param("   ", r"(?i)whitespace", id="whitespace_only"),
            pytest.param("\t\r\n", r"(?i)whitespace", id="control_characters"),
            pytest.param("https://example.com/foo bar", r"(?i)whitespace", id="unencoded_space"),
            pytest.param("https://example.com/\r\nSet-Cookie:bad", r"(?i)whitespace|crlf", id="crlf_injection"),
            pytest.param("https://example.com/path\x00extra", r"(?i)null|invalid", id="null_byte_injection"),

            # خطاهای Scheme / Protocol
            pytest.param("example.com", r"(?i)scheme", id="missing_scheme"),
            pytest.param("//example.com/path", r"(?i)scheme", id="protocol_relative"),
            pytest.param("ftp://example.com/dump", r"(?i)scheme|unsupported", id="disallowed_ftp"),
            pytest.param("javascript:alert(1)", r"(?i)scheme", id="xss_javascript_uri"),
            pytest.param("file:///etc/shadow", r"(?i)scheme", id="lfi_file_uri"),
            pytest.param("data:text/html;base64,PHNjcmlwdD4=", r"(?i)scheme", id="data_uri"),

            # خطاهای Host / Authority
            pytest.param("https://", r"(?i)host", id="missing_host_root"),
            pytest.param("https:///", r"(?i)host", id="missing_host_with_slash"),
            pytest.param("https://:8080", r"(?i)host", id="port_without_host"),
            pytest.param("https://[invalid:ipv6]:443", r"(?i)ipv6|host", id="malformed_ipv6"),

            # خطاهای Port
            pytest.param("https://example.com:0", r"(?i)port", id="port_zero"),
            pytest.param("https://example.com:65536", r"(?i)port", id="port_out_of_range"),
            pytest.param("https://example.com:badport", r"(?i)port", id="port_non_numeric"),

            # پایداری طول (DoS Protection)
            pytest.param(
                f"https://example.com/{'a' * (MAX_URL_LENGTH_OCTETS + 1)}",
                r"(?i)length|too long",
                id="url_length_exceeded",
            ),
        ],
    )
    def test_rejects_malformed_urls(self, url: str, err_regex: str) -> None:
        """بررسی برانگیختن دقیق استثنا و پیام خطا برای ورودی‌های نامعتبر."""
        with pytest.raises(ValidationError, match=err_regex):
            validate_url(url)
