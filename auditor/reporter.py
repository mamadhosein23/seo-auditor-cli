from __future__ import annotations

from pathlib import Path
from typing import Sequence, Iterator

from pydantic import TypeAdapter
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.panel import Panel

from auditor.parser import AuditResult

console = Console()
error_console = Console(stderr=True)

# Performance optimization: Module-level TypeAdapter
_AUDIT_RESULTS_ADAPTER: TypeAdapter[list[AuditResult]] = TypeAdapter(list[AuditResult])

def _format_metric(
    value: float | None,
    good_threshold: float,
    poor_threshold: float,
    unit: str = " ms",
    precision: int = 0,
) -> str:
    """Format Web Vitals using standard Google thresholds."""
    if value is None:
        return "[dim]—[/dim]"
    
    # Use color-coded thresholds for immediate visual feedback
    if value <= good_threshold:
        color = "green"
    elif value <= poor_threshold:
        color = "yellow"
    else:
        color = "red"
        
    return f"[{color}]{value:.{precision}f}{unit}[/{color}]"

def _format_status_code(code: int | None) -> str:
    """Colorize HTTP status codes."""
    if code is None:
        return "[dim]—[/dim]"
    
    color = "green" if 200 <= code < 300 else "yellow" if 300 <= code < 400 else "red"
    return f"[{color}]{code}[/{color}]"

def _iter_normalized(results: Sequence[AuditResult | Exception]) -> Iterator[AuditResult]:
    """Efficiently normalize results without duplicating memory."""
    for item in results:
        if isinstance(item, Exception):
            yield AuditResult(
                url="[Unknown Target]",
                errors=[f"Unhandled exception: {type(item).__name__}: {item}"]
            )
        else:
            yield item

def print_report(results: Sequence[AuditResult | Exception]) -> None:
    """Render a structured, color-coded report to the console."""
    table = Table(title="SEO & Performance Audit", header_style="bold cyan", expand=True)

    table.add_column("URL", overflow="fold", ratio=2)
    table.add_column("HTTP", justify="center")
    table.add_column("Title", overflow="ellipsis", ratio=1)
    table.add_column("No-Alt", justify="center")
    table.add_column("LCP", justify="right")
    table.add_column("CLS", justify="right")
    table.add_column("INP", justify="right")

    # Iterate through normalized data lazily
    audit_results = list(_iter_normalized(results))
    
    for res in audit_results:
        metrics = res.metrics
        table.add_row(
            escape(res.url),
            _format_status_code(res.status_code),
            escape(res.title) if res.title else "[dim]—[/dim]",
            f"[red]{res.images_without_alt}[/red]" if res.images_without_alt > 0 else "[green]0[/green]",
            _format_metric(metrics.lcp_ms, 2500, 4000),
            _format_metric(metrics.cls, 0.1, 0.25, unit="", precision=3),
            _format_metric(metrics.inp_ms, 200, 500),
        )

    console.print(table)

    # Clean summary of issues using Panels
    for res in audit_results:
        if res.errors or res.warnings:
            issues = [f"[bold red]ERR[/bold red] - {e}" for e in res.errors] + \
                     [f"[bold yellow]WRN[/bold yellow] - {w}" for w in res.warnings]
            error_console.print(Panel("\n".join(issues), title=f"[bold]{escape(res.url)}[/bold]", border_style="red"))

def save_json(results: Sequence[AuditResult | Exception], output_path: Path) -> None:
    """Serialize results to a formatted JSON file."""
    audit_results = list(_iter_normalized(results))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(_AUDIT_RESULTS_ADAPTER.dump_json(audit_results, indent=2) + b"\n")
