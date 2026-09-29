from urllib.parse import urlsplit

from playwright.async_api import Browser

from auditor.metrics import METRICS_INIT_SCRIPT, collect_metrics
from auditor.parser import AuditResult, parse_page


def validate_url(url: str) -> None:
    """Raise ValueError unless url is a valid HTTP(S) URL."""

    if not url or url != url.strip():
        raise ValueError("URL خالی است یا فاصلهٔ ابتدا/انتها دارد.")

    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        parsed.port  # بررسی معتبر بودن پورت
    except ValueError as exc:
        raise ValueError(f"URL نامعتبر است: {exc}") from exc

    if parsed.scheme not in {"http", "https"} or not hostname:
        raise ValueError("URL باید کامل و با http:// یا https:// شروع شود.")


async def audit_url(
    browser: Browser,
    url: str,
    timeout_ms: int = 30_000,
    settle_ms: int = 2_000,
) -> AuditResult:
    """Open a URL, inspect its DOM and collect browser performance metrics."""

    try:
        validate_url(url)
    except ValueError as exc:
        return AuditResult(url=url, errors=[str(exc)])

    context = None

    try:
        context = await browser.new_context()
        page = await context.new_page()
        await page.add_init_script(METRICS_INIT_SCRIPT)

        response = await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=timeout_ms,
        )

        # Give browser performance observers a little time to receive entries.
        if settle_ms > 0:
            await page.wait_for_timeout(settle_ms)

        result = await parse_page(
            page=page,
            requested_url=url,
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
