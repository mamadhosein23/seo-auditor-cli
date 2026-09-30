from pathlib import Path
from typing import Sequence

from pydantic import TypeAdapter
from rich.console import Console
from rich.table import Table

from auditor.parser import AuditResult

console = Console()
error_console = Console(stderr=True)


def _format_lcp(value: float | None) -> str:
    if value is None:
        return "[dim]—[/dim]"
    color = "green" if value <= 2500 else "yellow" if value <= 4000 else "red"
    return f"[{color}]{value:.0f} ms[/{color}]"


def _format_cls(value: float | None) -> str:
    if value is None:
        return "[dim]—[/dim]"
    color = "green" if value <= 0.1 else "yellow" if value <= 0.25 else "red"
    return f"[{color}]{value:.3f}[/{color}]"


def _format_inp(value: float | None) -> str:
    if value is None:
        return "[dim]—[/dim]"
    color = "green" if value <= 200 else "yellow" if value <= 500 else "red"
    return f"[{color}]{value:.0f} ms[/{color}]"


def print_report(results: Sequence[AuditResult]) -> None:
    table = Table(title="SEO & Performance Audit", header_style="bold cyan")

    table.add_column("URL", overflow="fold", no_wrap=False)
    table.add_column("HTTP", justify="right")
    table.add_column("Title", overflow="ellipsis", max_width=40)
    table.add_column("LCP", justify="right")
    table.add_column("CLS", justify="right")
    table.add_column("INP", justify="right")

    for result in results:
        status = (
            f"[green]{result.status_code}[/green]"
            if result.status_code and result.status_code < 400
            else f"[red]{result.status_code or '—'}[/red]"
        )
        table.add_row(
            result.url,
            status,
            result.title or "[dim]—[/dim]",
            _format_lcp(result.metrics.lcp_ms),
            _format_cls(result.metrics.cls),
            _format_inp(result.metrics.inp_ms),
        )

    console.print(table)

    # ارسال خطاها و هشدارها به stderr
    for result in results:
        for error in result.errors:
            error_console.print(f"[bold red]خطا[/bold red] — {result.url}: {error}")
        for warning in result.warnings:
            error_console.print(f"[bold yellow]هشدار[/bold yellow] — {result.url}: {warning}")


def save_json(results: Sequence[AuditResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # سریال‌سازی بهینه و مستقیم به JSON در Pydantic v2 بدون سربار دیکشنری میانی
    adapter = TypeAdapter(list[AuditResult])
    json_bytes = adapter.dump_json(results, indent=2)
    output_path.write_bytes(json_bytes)
