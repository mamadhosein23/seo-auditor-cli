import pytest

from auditor.engine import validate_url


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "http://example.com/page?id=1",
        "https://sub.example.com:8443/path",
    ],
)
def test_accepts_valid_http_urls(url: str) -> None:
    validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "",
        " example.com ",
        "example.com",
        "ftp://example.com",
        "https://",
        "https://example.com:invalid",
    ],
)
def test_rejects_invalid_urls(url: str) -> None:
    with pytest.raises(ValueError):
        validate_url(url)
