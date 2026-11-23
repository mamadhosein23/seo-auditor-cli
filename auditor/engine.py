from __future__ import annotations

from urllib.parse import urlsplit

from playwright.async_api import Browser, Error as PlaywrightError

from auditor.metrics import METRICS_INIT_SCRIPT, collect_metrics
from auditor.parser import AuditResult, parse_page


def validate_url(url: str) -> str:
    """Validate and return an absolute HTTP(S) URL."""
    if not isinstance(url, str):
        raise TypeError(f"URL must be a string, got {type(url).__name__}")

    if not url:
        raise ValueError("URL cannot be empty")

    if not url.strip():
        raise ValueError("URL cannot be whitespace-only")

    if any(char.isspace() for char in url):
        raise ValueError("URL contains illegal whitespace characters")

    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port  # Raises ValueError if the port is malformed.
    except ValueError as exc:
        raise ValueError(f"Invalid URL: {exc}") from exc

    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError(
            f"Unsupported scheme: '{parsed.scheme}'. Only http/https allowed."
        )

    if not parsed.netloc or not hostname:
        raise ValueError("Missing host in URL")

    if port is not None and not (1 <= port <= 65535):
        raise ValueError(f"URL port out of range: {port}")

    return url


async def audit_url(
    browser: Browser,
    url: str,
    timeout_ms: int = 30_000,
    settle_ms: int = 2_000,
) -> AuditResult:
    """Open a URL, inspect its DOM, and collect performance metrics."""
    try:
        validated_url = validate_url(url)
    except (TypeError, ValueError) as exc:
        return AuditResult(url=url, errors=[str(exc)])

    try:
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (compatible; SEOAuditorBot/1.0; "
                "+https://example.com/bot)"
            ),
            viewport={"width": 1280, "height": 800},
        )

        try:
            page = await context.new_page()

            try:
                await page.add_init_script(METRICS_INIT_SCRIPT)

                response = await page.goto(
                    validated_url,
                    wait_until="domcontentloaded",
                    timeout=timeout_ms,
                )

                errors: list[str] = []
                status_code = response.status if response is not None else None

                if response is None:
                    errors.append("Navigation failed: No HTTP response received.")
                elif status_code >= 400:
                    errors.append(f"HTTP error status: {status_code}")

                if settle_ms > 0:
                    await page.wait_for_timeout(settle_ms)

                result = await parse_page(page, validated_url, status_code)

                result.errors.extend(errors)
                result.metrics = await collect_metrics(page)
                return result

            finally:
                await page.close()

        finally:
            await context.close()

    except PlaywrightError as exc:
        return AuditResult(url=url, errors=[f"BrowserError: {exc.message}"])
    except Exception as exc:
        return AuditResult(url=url, errors=[f"{type(exc).__name__}: {exc}"])
