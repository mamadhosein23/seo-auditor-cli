"""Unit tests for the URL validation engine."""

from __future__ import annotations

from typing import Any

import pytest

from auditor.engine import validate_url


class TestValidateUrlSuccess:
    """Suite for validating correct URL formats."""

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
            pytest.param("https://user:https://user:secret-token@@example.com/protected", id="basic_auth_url"),
        ],
    )
    def test_accepts_valid_urls(self, url: str) -> None:
        """Ensure valid URLs are returned unmodified."""
        assert validate_url(url) == url


class TestValidateUrlValueFailures:
    """Suite for validating error handling of malformed URL strings."""

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
    def test_rejects_invalid_url_values(self, url: str, error_pattern: str) -> None:
        """Ensure malformed strings raise ValueError with descriptive messages."""
        with pytest.raises(ValueError, match=error_pattern):
            validate_url(url)


class TestValidateUrlTypeFailures:
    """Suite for validating type safety and input sanitization."""

    @pytest.mark.parametrize(
        "invalid_input",
        [
            pytest.param(None, id="none_type"),
            pytest.param(12345, id="integer_type"),
            pytest.param(b"https://example.com", id="bytes_type"),
            pytest.param(["https://example.com"], id="list_type"),
        ],
    )
    def test_rejects_non_string_types(self, invalid_input: Any) -> None:
        """Ensure non-string types raise TypeError."""
        with pytest.raises(TypeError, match=r"(?i)must be a string"):
            validate_url(invalid_input)
