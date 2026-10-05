from pathlib import Path
from typing import Sequence

from pydantic import TypeAdapter
from rich.console import Console
from rich.table import Table

from auditor.parser import AuditResult

console = Console()
error_console = Console(stderr=True)

# بهینه‌سازی: تعریف آداپتور در سطح ماژول جهت جلوگیری از بازسازی مکرر Schema
_AUDIT_RESULTS_ADAPTER: TypeAdapter[list[AuditResult]] = TypeAdapter(list[AuditResult])


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
        # مدیریت خطای None بودن آبجکت metrics در صورت خرابی لود صفحه
        metrics = getattr(result, "metrics", None)
        lcp = getattr(metrics, "lcp_ms", None) if metrics else None
        cls = getattr(metrics, "cls", None) if metrics else None
        inp = getattr(metrics, "inp_ms", None) if metrics else None

        table.add_row(
            result.url,
            _format_status_code(result.status_code),
            result.title or "[dim]—[/dim]",
            _format_metric(lcp, 2500, 4000),
            _format_metric(cls, 0.1, 0.25, unit="", precision=3),
            _format_metric(inp, 200, 500),
        )

    console.print(table)

    # نمایش خطاها و هشدارها به تفکیک روی stderr
    for result in results:
        for error in getattr(result, "errors", []):
            error_console.print(f"[bold red]ERROR[/bold red]   — {result.url}: {error}")
        for warning in getattr(result, "warnings", []):
            error_console.print(f"[bold yellow]WARNING[/bold yellow] — {result.url}: {warning}")


def save_json(results: Sequence[AuditResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # استفاده از آداپتور کش‌شده ماژول
    json_bytes = _AUDIT_RESULTS_ADAPTER.dump_json(list(results), indent=2)
    output_path.write_bytes(json_bytes + b"\n")
