from __future__ import annotations

from typing import Optional
from urllib.parse import urlsplit

from playwright.async_api import Browser, Page, Error as PlaywrightError

from auditor.metrics import METRICS_INIT_SCRIPT, collect_metrics
from auditor.parser import AuditResult, parse_page

def validate_url(url: str) -> str:
    """Validate and return the URL. Raise TypeError or ValueError if invalid."""
    if not isinstance(url, str):
        raise TypeError(f"URL must be a string, got {type(url).__name__}")
    
    if not url.strip():
        raise ValueError("URL cannot be empty or whitespace-only")
    
    if any(c.isspace() for c in url):
        raise ValueError("URL contains illegal whitespace characters")

    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported scheme: '{parsed.scheme}'. Only http/https allowed.")
    
    if not parsed.hostname:
        raise ValueError("Missing host in URL")
        
    if parsed.port and not (1 <= parsed.port <= 65535):
        raise ValueError(f"URL port out of range: {parsed.port}")

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
    except (ValueError, TypeError) as exc:
        return AuditResult(url=url, errors=[str(exc)])

    # Using async context managers for clean resource lifecycle management
    async with await browser.new_context(
        user_agent="Mozilla/5.0 (compatible; SEOAuditorBot/1.0; +https://example.com/bot)",
        viewport={"width": 1280, "height": 800},
    ) as context:
        async with await context.new_page() as page:
            try:
                await page.add_init_script(METRICS_INIT_SCRIPT)
                
                response = await page.goto(
                    validated_url,
                    wait_until="domcontentloaded",
                    timeout=timeout_ms,
                )

                errors: list[str] = []
                status_code = response.status if response else None

                if not response:
                    errors.append("Navigation failed: No HTTP response received.")
                elif status_code and status_code >= 400:
                    errors.append(f"HTTP error status: {status_code}")

                if settle_ms > 0:
                    await page.wait_for_timeout(settle_ms)

                result = await parse_page(page, validated_url, status_code)
                
                if errors:
                    result.errors.extend(errors)
                
                result.metrics = await collect_metrics(page)
                return result

            except PlaywrightError as exc:
                return AuditResult(url=url, errors=[f"BrowserError: {exc.message}"])
            except Exception as exc:
                return AuditResult(url=url, errors=[f"{type(exc).__name__}: {exc}"])
