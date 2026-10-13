from typing import Any
import pytest

from auditor.engine import validate_url


class TestValidateUrlSuccess:
    """Test suite for valid URLs across protocols, encodings, and network formats."""

    @pytest.mark.parametrize(
        ("url", "scenario_id"),
        [
            ("https://example.com", "standard_https"),
            ("http://example.com/page?id=1", "query_parameters"),
            ("https://sub.example.com:8443/path", "custom_tls_port"),
            ("https://example.com/search?q=test#section", "url_fragment"),
            ("https://xn--bcher-kva.example", "punycode_idn"),
            ("http://[::1]:8080/path", "ipv6_loopback"),
            ("http://127.0.0.1:3000/api", "ipv4_address"),
            ("https://user:pass@example.com/protected", "basic_auth_url"),
        ],
        ids=lambda param: param if isinstance(param, str) and not param.startswith("http") else None,
    )
    def test_accepts_valid_http_urls(self, url: str, scenario_id: str) -> None:
        result = validate_url(url)
        assert result == url
        assert isinstance(result, str)


class TestValidateUrlValueFailures:
    """Test suite ensuring strictly rejected malformed or invalid URLs."""

    @pytest.mark.parametrize(
        ("url", "error_pattern"),
        [
            # Empty / Pure whitespace
            pytest.param("", r"cannot be empty", id="empty_string"),
            pytest.param("   ", r"whitespace", id="spaces_only"),
            pytest.param("\t\n", r"whitespace", id="whitespace_control_characters"),

            # Whitespace inside URL (injection / browser-split prevention)
            pytest.param("https://example.com/foo bar", r"whitespace", id="inline_space"),
            pytest.param("https://example.com/\r\npage", r"whitespace", id="crlf_injection_vector"),

            # Missing or unsupported protocol schemas
            pytest.param("example.com", r"scheme", id="missing_scheme"),
            pytest.param("//example.com/path", r"scheme", id="protocol_relative_disallowed"),
            pytest.param("ftp://example.com", r"scheme", id="ftp_scheme"),
            pytest.param("javascript:alert(1)", r"scheme", id="javascript_pseudo_protocol"),
            pytest.param("file:///etc/passwd", r"scheme", id="local_file_scheme"),
            pytest.param("data:text/html,payload", r"scheme", id="data_uri"),

            # Host issues
            pytest.param("https://", r"host", id="missing_host_root"),
            pytest.param("https:///", r"host", id="missing_host_with_slash"),
            pytest.param("https://:8080", r"host", id="port_without_host"),

            # Port range & type validation
            pytest.param("https://example.com:invalid", r"port", id="port_non_numeric"),
            pytest.param("https://example.com:0", r"port", id="port_zero_invalid"),
            pytest.param("https://example.com:65536", r"port", id="port_exceeds_uint16"),
            pytest.param("https://example.com:-1", r"port", id="port_negative"),
        ],
    )
    def test_rejects_invalid_urls(self, url: str, error_pattern: str) -> None:
        with pytest.raises(ValueError, match=rf"(?i){error_pattern}"):
            validate_url(url)


class TestValidateUrlTypeFailures:
    """Boundary type checks enforcing strict runtime interface contracts."""

    @pytest.mark.parametrize(
        "invalid_input",
        [
            pytest.param(None, id="none_type"),
            pytest.param(12345, id="integer_type"),
            pytest.param(42.0, id="float_type"),
            pytest.param([], id="list_type"),
            pytest.param({}, id="dict_type"),
            pytest.param(b"https://example.com", id="raw_bytes_not_str"),
        ],
    )
    def test_rejects_non_string_types(self, invalid_input: Any) -> None:
        with pytest.raises(TypeError, match=r"(?i)must be a string"):
            validate_url(invalid_input)
