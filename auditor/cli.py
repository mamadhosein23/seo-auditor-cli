# tests/test_validator.py
import re
from typing import Final

import pytest

from auditor.engine import validate_url


class TestValidateUrlSuccess:
    """Test valid URLs across protocols, encodings, and network formats."""

    @pytest.mark.parametrize(
        ("url", "scenario_id"),
        [
            pytest.param("https://example.com", "standard_https", id="standard_https"),
            pytest.param("http://example.com/page?id=1", "query_parameters", id="query_parameters"),
            pytest.param("https://sub.example.com:8443/path", "custom_tls_port", id="custom_tls_port"),
            pytest.param("https://example.com/search?q=test#section", "url_fragment", id="url_fragment"),
            pytest.param("https://xn--bcher-kva.example", "punycode_idn", id="punycode_idn"),
            pytest.param("http://[::1]:8080/path", "ipv6_loopback", id="ipv6_loopback"),
            pytest.param("http://127.0.0.1:3000/api", "ipv4_address", id="ipv4_address"),
            pytest.param("https://user:token@example.com/protected", "basic_auth_url", id="basic_auth_url"),
        ],
    )
    def test_accepts_valid_http_urls(self, url: str, scenario_id: str) -> None:
        result = validate_url(url)
        assert result == url
        assert isinstance(result, str)


class TestValidateUrlValueFailures:
    """Test rejection of malformed or invalid URLs against explicit error patterns."""

    @pytest.mark.parametrize(
        ("url", "error_pattern"),
        [
            pytest.param("", r"cannot be empty", id="empty_string"),
            pytest.param("   ", r"whitespace", id="spaces_only"),
            pytest.param("\t\n", r"whitespace", id="whitespace_control_characters"),
            pytest.param("https://example.com/foo bar", r"whitespace", id="inline_space"),
            pytest.param("https://example.com/\r\npage", r"whitespace", id="crlf_injection_vector"),
            pytest.param("example.com", r"scheme", id="missing_scheme"),
            pytest.param("//example.com/path", r"scheme", id="protocol_relative_disallowed"),
            pytest.param("ftp://example.com", r"scheme", id="ftp_scheme"),
            pytest.param("javascript:alert(1)", r"scheme", id="javascript_pseudo_protocol"),
            pytest.param("file:///etc/passwd", r"scheme", id="local_file_scheme"),
            pytest.param("data:text/html,payload", r"scheme", id="data_uri"),
            pytest.param("https://", r"host", id="missing_host_root"),
            pytest.param("https:///", r"host", id="missing_host_with_slash"),
        ],
    )
    def test_rejects_invalid_urls(self, url: str, error_pattern: str) -> None:
        with pytest.raises(ValueError, match=re.compile(error_pattern, re.IGNORECASE)):
            validate_url(url)
