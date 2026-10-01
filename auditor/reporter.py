from pathlib import Path
from typing import Sequence

from pydantic import TypeAdapter
from rich.console import Console
from rich.table import Table

from auditor.parser import AuditResult

console = Console()
error_console = Console(stderr=True)


def _format_metric(
    value: float | None,
    good_threshold: float,
    poor_threshold: float,
    unit: str = " ms",
    precision: int = 0,
) -> str:
    """فرمت‌دهی یکپارچه متریک‌های Web Vitals بر اساس آستانه‌های رسمی گوگل."""
    if value is None:
        return "[dim]—[/dim]"
    color = "green" if value <= good_threshold else "yellow" if value <= poor_threshold else "red"
    return f"[{color}]{value:.{precision}f}{unit}[/{color}]"


def _format_status_code(code: int | None) -> str:
    """رنگ‌آمیزی استاندارد کدهای وضعیت HTTP بر اساس رنج عددی."""
    if code is None:
        return "[dim]—[/dim]"
    if 200 <= code < 300:
        return f"[green]{code}[/green]"
    if 300 <= code < 400:
        return f"[yellow]{code}[/yellow]"
    return f"[red]{code}[/red]"


def print_report(results: Sequence[AuditResult]) -> None:
    table = Table(title="SEO & Performance Audit", header_style="bold cyan")

    table.add_column("URL", overflow="fold", no_wrap=False)
    table.add_column("HTTP", justify="right")
    table.add_column("Title", overflow="ellipsis", max_width=40)
    table.add_column("LCP", justify="right")
    table.add_column("CLS", justify="right")
    table.add_column("INP", justify="right")

    for result in results:
        table.add_row(
            result.url,
            _format_status_code(result.status_code),
            result.title or "[dim]—[/dim]",
            _format_metric(result.metrics.lcp_ms, 2500, 4000),
            _format_metric(result.metrics.cls, 0.1, 0.25, unit="", precision=3),
            _format_metric(result.metrics.inp_ms, 200, 500),
        )

    console.print(table)

    # نمایش خطاها و هشدارها به تفکیک روی stderr
    for result in results:
        for error in result.errors:
            error_console.print(f"[bold red]ERROR[/bold red]   — {result.url}: {error}")
        for warning in result.warnings:
            error_console.print(f"[bold yellow]WARNING[/bold yellow] — {result.url}: {warning}")


def save_json(results: Sequence[AuditResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    adapter = TypeAdapter(list[AuditResult])
    json_bytes = adapter.dump_json(results, indent=2)
    output_path.write_bytes(json_bytes)
