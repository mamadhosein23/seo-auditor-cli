from urllib.parse import urlsplit
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, Error as PlaywrightError

from auditor.metrics import METRICS_INIT_SCRIPT, collect_metrics
from auditor.parser import AuditResult, parse_page


def validate_url(url: str) -> str:
    """Validate and return the URL. Raise TypeError or ValueError if invalid."""
    if not isinstance(url, str):
        raise TypeError(f"URL must be a string, got {type(url).__name__}")

    if not url:
        raise ValueError("URL cannot be empty")

    if any(c.isspace() for c in url):
        raise ValueError("URL contains whitespace characters")

    try:
        parsed = urlsplit(url)
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

    context: Optional[BrowserContext] = None
    page: Optional[Page] = None

    try:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (compatible; SEOAuditorBot/1.0; +https://example.com/bot)",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        
        # Inject performance observer scripts before page scripts execute
        await page.add_init_script(METRICS_INIT_SCRIPT)

        response = await page.goto(
            validated_url,
            wait_until="domcontentloaded",
            timeout=timeout_ms,
        )

        errors: list[str] = []
        status_code: Optional[int] = None

        if response is None:
            errors.append("Navigation succeeded but no HTTP response was received (e.g. data URL or aborted).")
        else:
            status_code = response.status
            if status_code >= 400:
                errors.append(f"HTTP response error status: {status_code}")

        # Allow layout shifts and paint observers to settle
        if settle_ms > 0:
            await page.wait_for_timeout(settle_ms)

        result = await parse_page(
            page=page,
            requested_url=validated_url,
            status_code=status_code,
        )
        
        # Append connection-level errors if any were collected
        if errors:
            result.errors.extend(errors)

        result.metrics = await collect_metrics(page)
        return result

    except PlaywrightError as exc:
        return AuditResult(
            url=url,
            errors=[f"BrowserError: {exc.message}"],
        )
    except Exception as exc:
        return AuditResult(
            url=url,
            errors=[f"{type(exc).__name__}: {exc}"],
        )

    finally:
        if page is not None:
            try:
                await page.close()
            except Exception:
                pass
        if context is not None:
            try:
                await context.close()
            except Exception:
                pass
