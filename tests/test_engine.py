from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from auditor.engine import ValidationError, validate_url

if TYPE_CHECKING:
    from typing import Final


class TestValidateUrlSuccess:
    """Validate RFC 3986 compliant HTTP/S URI patterns across edge cases."""

    @pytest.mark.parametrize(
        ("url", "scenario_id"),
        [
            pytest.param(
                "https://example.com",
                "standard_https",
                id="standard_https",
            ),
            pytest.param(
                "http://example.com/page?id=1&category=books",
                "query_parameters_multi",
                id="query_parameters_multi",
            ),
            pytest.param(
                "https://sub.example.com:8443/api/v1/health",
                "custom_tls_port",
                id="custom_tls_port",
            ),
            pytest.param(
                "https://example.com/search?q=test#section-2",
                "url_with_fragment",
                id="url_with_fragment",
            ),
            pytest.param(
                "https://xn--bcher-kva.example",
                "punycode_idn_domain",
                id="punycode_idn_domain",
            ),
            pytest.param(
                "http://[::1]:8080/metrics",
                "ipv6_loopback_explicit_port",
                id="ipv6_loopback_explicit_port",
            ),
            pytest.param(
                "http://127.0.0.1:3000/api/v1",
                "ipv4_loopback_explicit_port",
                id="ipv4_loopback_explicit_port",
            ),
            pytest.param(
                "https://user:secret-token@example.com/protected",
                "rfc3986_userinfo_credentials",
                id="rfc3986_userinfo_credentials",
            ),
            pytest.param(
                "https://example.com:443/",
                "explicit_default_tls_port",
                id="explicit_default_tls_port",
            ),
            pytest.param(
                "https://example.com/%F0%9F%A6%80",
                "percent_encoded_utf8_path",
                id="percent_encoded_utf8_path",
            ),
        ],
    )
    def test_accepts_valid_http_urls(self, url: str, scenario_id: str) -> None:
        """Ensure conformant HTTP/HTTPS URLs pass validation without mutations."""
        result: str = validate_url(url)
        assert result == url
        assert isinstance(result, str)


class TestValidateUrlFailures:
    """Test boundary enforcement, malicious payloads, and malformed structures."""

    @pytest.mark.parametrize(
        ("url", "expected_pattern"),
        [
            # Zero-length & Whitespace variants
            pytest.param("", r"(?i)empty", id="empty_string"),
            pytest.param("   ", r"(?i)whitespace", id="spaces_only"),
            pytest.param("\t\n", r"(?i)whitespace", id="whitespace_control_characters"),
            pytest.param("https://example.com/foo bar", r"(?i)whitespace", id="unencoded_space_path"),
            pytest.param("https://example.com/\r\npage", r"(?i)whitespace|crlf", id="crlf_header_injection"),

            # Scheme Violations
            pytest.param("example.com", r"(?i)scheme", id="missing_scheme"),
            pytest.param("//example.com/path", r"(?i)scheme", id="protocol_relative"),
            pytest.param("ftp://example.com", r"(?i)scheme", id="unsupported_ftp_scheme"),
            pytest.param("file:///etc/passwd", r"(?i)scheme", id="local_filesystem_scheme"),
            pytest.param("javascript:alert(1)", r"(?i)scheme", id="pseudo_protocol_xss"),
            pytest.param("data:text/html,<script>alert(1)</script>", r"(?i)scheme", id="data_uri_scheme"),

            # Authority & Host Integrity
            pytest.param("https://", r"(?i)host", id="missing_host_root"),
            pytest.param("https:///", r"(?i)host", id="missing_host_trailing_slash"),
            pytest.param("https://:8080/path", r"(?i)host", id="port_without_host"),
            pytest.param("https://example.com:65536/", r"(?i)port", id="port_overflow_above_uint16"),
            pytest.param("https://example.com:-1/", r"(?i)port", id="negative_port_number"),

            # Security Vectors: Null-Byte & SSRF Evasion Ambiguities
            pytest.param("https://example.com\x00/admin", r"(?i)null|invalid", id="null_byte_path_injection"),
            pytest.param("https://attacker.com#@example.com", r"(?i)host|authority", id="authority_fragment_confusion"),
        ],
    )
    def test_rejects_malformed_and_exploit_urls(
        self,
        url: str,
        expected_pattern: str,
    ) -> None:
        """Ensure invalid URIs raise appropriate domain exceptions matching regex specifications."""
        with pytest.raises(ValidationError, match=expected_pattern):
            validate_url(url)
