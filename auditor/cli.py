# tests/test_validator.py
from __future__ import annotations

import pytest

from auditor.engine import validate_url


class TestValidateUrlSuccess:
    """Test valid URLs across protocols, encodings, and network formats."""

    @pytest.mark.parametrize(
        "url",
        [
            pytest.param("https://example.com", id="standard_https"),
            pytest.param("http://example.com/page?id=1", id="query_parameters"),
            pytest.param("https://sub.example.com:8443/path", id="custom_tls_port"),
            pytest.param("https://example.com/search?q=test#section", id="url_fragment"),
            pytest.param("https://xn--bcher-kva.example", id="punycode_idn"),
            pytest.param("http://[::1]:8080/path", id="ipv6_loopback"),
            pytest.param("http://127.0.0.1:3000/api", id="ipv4_address"),
            pytest.param("https://user:secret-token@example.com/protected", id="basic_auth_url"),
        ],
    )
    def test_accepts_valid_http_urls(self, url: str) -> None:
        result = validate_url(url)
        assert result == url
        assert isinstance(result, str)


class TestValidateUrlValueFailures:
    """Test rejection of malformed or invalid URLs against explicit error patterns."""

    @pytest.mark.parametrize(
        ("url", "error_pattern"),
        [
            pytest.param("", r"(?i)cannot be empty", id="empty_string"),
            pytest.param("   ", r"(?i)whitespace", id="spaces_only"),
            pytest.param("\t\n", r"(?i)whitespace", id="whitespace_control_characters"),
            pytest.param("https://example.com/foo bar", r"(?i)whitespace", id="inline_space"),
            pytest.param("https://example.com/\r\npage", r"(?i)whitespace", id="crlf_injection_vector"),
            pytest.param("example.com", r"(?i)scheme", id="missing_scheme"),
            pytest.param("//example.com/path", r"(?i)scheme", id="protocol_relative_disallowed"),
            pytest.param("ftp://example.com", r"(?i)scheme", id="ftp_scheme"),
            pytest.param("javascript:alert(1)", r"(?i)scheme", id="javascript_pseudo_protocol"),
            pytest.param("file:///etc/passwd", r"(?i)scheme", id="local_file_scheme"),
            pytest.param("data:text/html,payload", r"(?i)scheme", id="data_uri"),
            pytest.param("https://", r"(?i)host", id="missing_host_root"),
            pytest.param("https:///", r"(?i)host", id="missing_host_with_slash"),
        ],
    )
    def test_rejects_invalid_urls(self, url: str, error_pattern: str) -> None:
        with pytest.raises(ValueError, match=error_pattern):
            validate_url(url)
