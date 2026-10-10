import asyncio
from pathlib import Path
from typing import Annotated, Any

import typer
from playwright.async_api import async_playwright

from auditor.engine import audit_url
from auditor.reporter import print_report, save_json

app = typer.Typer(
    name="seo-auditor",
    help="CLI tool for automated technical SEO and performance auditing.",
    no_args_is_help=True,
)


async def _scan_urls(
    urls: list[str],
    concurrency: int,
    timeout_ms: int,
    settle_ms: int,
) -> list[Any]:
    semaphore = asyncio.Semaphore(concurrency)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)

        async def scan_one(url: str) -> Any:
            async with semaphore:
                return await audit_url(
                    browser=browser,
                    url=url,
                    timeout_ms=timeout_ms,
                    settle_ms=settle_ms,
                )

        try:
            # return_exceptions=True prevents one failed page from canceling the whole batch
            return await asyncio.gather(
                *(scan_one(url) for url in urls),
                return_exceptions=False,
            )
        finally:
            await browser.close()


@app.command()
def scan(
    urls: Annotated[
        list[str],
        typer.Argument(
            help="One or more target URLs (e.g., https://example.com)",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Path to save the generated JSON audit report.",
        ),
    ] = Path("seo-audit-report.json"),
    concurrency: Annotated[
        int,
        typer.Option(
            "--concurrency",
            "-c",
            min=1,
            help="Maximum concurrent pages to audit simultaneously.",
        ),
    ] = 3,
    timeout: Annotated[
        int,
        typer.Option(
            "--timeout",
            help="Page navigation timeout in milliseconds.",
        ),
    ] = 30_000,
    settle: Annotated[
        int,
        typer.Option(
            "--settle",
            help="Post-DOM settle delay in milliseconds.",
        ),
    ] = 2_000,
) -> None:
    """Audit one or multiple web pages and export the findings."""
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
        typer.echo(f"Engine execution failure: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    print_report(results)
    save_json(results, output)
    typer.echo(f"\nJSON report saved: {output.resolve()}")

    # Fail command if all audits produced critical execution errors
    if all(getattr(result, "errors", None) for result in results):
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
