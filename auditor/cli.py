import asyncio
from pathlib import Path

import typer
from playwright.async_api import async_playwright

from auditor.engine import audit_url
from auditor.reporter import print_report, save_json


app = typer.Typer(
    name="seo-auditor",
    help="ابزار خط فرمان برای بررسی اولیه SEO و عملکرد صفحه.",
    no_args_is_help=True,
)


async def _scan_urls(
    urls: list[str],
    concurrency: int,
    timeout_ms: int,
    settle_ms: int,
):
    semaphore = asyncio.Semaphore(concurrency)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)

        async def scan_one(url: str):
            async with semaphore:
                return await audit_url(
                    browser=browser,
                    url=url,
                    timeout_ms=timeout_ms,
                    settle_ms=settle_ms,
                )

        try:
            return await asyncio.gather(*(scan_one(url) for url in urls))
        finally:
            await browser.close()


@app.command()
def scan(
    urls: list[str] = typer.Argument(
        ...,
        help="یک یا چند URL کامل، مانند https://example.com",
    ),
    output: Path = typer.Option(
        Path("seo-audit-report.json"),
        "--output",
        "-o",
        help="مسیر فایل گزارش JSON",
    ),
    concurrency: int = typer.Option(
        3,
        "--concurrency",
        "-c",
        min=1,
        help="حداکثر تعداد صفحه‌هایی که هم‌زمان بررسی می‌شوند.",
    ),
    timeout: int = typer.Option(
        30_000,
        "--timeout",
        help="مهلت بارگذاری هر صفحه برحسب میلی‌ثانیه.",
    ),
    settle: int = typer.Option(
        2_000,
        "--settle",
        help="زمان انتظار پس از بارگذاری DOM برحسب میلی‌ثانیه.",
    ),
) -> None:
    """بررسی یک یا چند صفحه و ذخیرهٔ گزارش."""

    try:
        results = asyncio.run(
            _scan_urls(
                urls=urls,
                concurrency=concurrency,
                timeout_ms=timeout,
                settle_ms=settle,
            )
        )
    except Exception as exc:
        typer.echo(f"خطا در اجرای Chromium: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    print_report(results)
    save_json(results, output)
    typer.echo(f"\nگزارش JSON ذخیره شد: {output}")

    if all(result.errors for result in results):
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
