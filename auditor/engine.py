from urllib.parse import urlsplit

from playwright.async_api import Browser

from auditor.metrics import METRICS_INIT_SCRIPT, collect_metrics
from auditor.parser import AuditResult, parse_page


def validate_url(url: str) -> str:
    """Validate and return the URL. Raise TypeError or ValueError if invalid."""
    if not isinstance(url, str):
        raise TypeError(f"URL must be a string, got {type(url).__name__}")

    if not url:
        raise ValueError("URL cannot be empty")

    if url != url.strip():
        raise ValueError("URL contains leading or trailing whitespaces")

    try:
        parsed = urlsplit(url)
        # Accessing port triggers parsing; validates numeric conversion
        port = parsed.port
        hostname = parsed.hostname
    except ValueError as exc:
        raise ValueError(f"Invalid URL port or structure: {exc}") from exc

    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported or missing scheme: '{parsed.scheme}'")

    if not hostname:
        raise ValueError("Missing host or netloc in URL")

    if port is not None and not (1 <= port <= 65535):
        raise ValueError(f"URL port out of range: {port}")

    return url


async def audit_url(
    browser: Browser,
    url: str,
    timeout_ms: int = 30_000,
    settle_ms: int = 2_000,
) -> AuditResult:
    """Open a URL, inspect its DOM, and collect browser performance metrics."""
    try:
        validated_url = validate_url(url)
    except (ValueError, TypeError) as exc:
        return AuditResult(url=url, errors=[str(exc)])

    context = None
    try:
        context = await browser.new_context()
        page = await context.new_page()
        await page.add_init_script(METRICS_INIT_SCRIPT)

        response = await page.goto(
            validated_url,
            wait_until="domcontentloaded",
            timeout=timeout_ms,
        )

        # Allow browser performance observers to capture runtime metrics
        if settle_ms > 0:
            await page.wait_for_timeout(settle_ms)

        result = await parse_page(
            page=page,
            requested_url=validated_url,
            status_code=response.status if response else None,
        )
        result.metrics = await collect_metrics(page)
        return result

    except Exception as exc:
        return AuditResult(
            url=url,
            errors=[f"{type(exc).__name__}: {exc}"],
        )

    finally:
        if context is not None:
            try:
                await context.close()
            except Exception:
                pass
