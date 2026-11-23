
from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import TypeAlias

from pydantic import TypeAdapter
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from auditor.parser import AuditResult

AuditItem: TypeAlias = AuditResult | Exception

console = Console()
error_console = Console(stderr=True)
_AUDIT_RESULTS_ADAPTER = TypeAdapter(list[AuditResult])


def _format_metric(
    value: float | None,
    good_threshold: float,
    poor_threshold: float,
    unit: str = " ms",
    precision: int = 0,
) -> str:
    """Format a metric according to its good, warning, and poor ranges."""
    if value is None:
        return "[dim]—[/dim]"

    if value <= good_threshold:
        color = "green"
    elif value <= poor_threshold:
        color = "yellow"
    else:
        color = "red"

    return f"[{color}]{value:.{precision}f}{unit}[/{color}]"


def _format_status_code(code: int | None) -> str:
    """Return a colorized HTTP status code."""
    if code is None:
        return "[dim]—[/dim]"

    color = "green" if 200 <= code < 300 else "yellow" if 300 <= code < 400 else "red"
    return f"[{color}]{code}[/{color}]"


def _iter_normalized(results: Sequence[AuditItem]) -> Iterator[AuditResult]:
    """Convert exceptions into serializable audit results."""
    for item in results:
        if isinstance(item, Exception):
            yield AuditResult(
                url="[Unknown Target]",
                errors=[f"Unhandled exception: {type(item).__name__}: {item}"],
            )
        else:
            yield item


def print_report(results: Sequence[AuditItem]) -> None:
    """Render a color-coded audit table and issue panels."""
    audit_results = list(_iter_normalized(results))
    table = Table(
        title="SEO & Performance Audit",
        header_style="bold cyan",
        expand=True,
    )
    table.add_column("URL", overflow="fold", ratio=2)
    table.add_column("HTTP", justify="center")
    table.add_column("Title", overflow="ellipsis", ratio=1)
    table.add_column("Missing Alt", justify="center")
    table.add_column("LCP", justify="right")
    table.add_column("CLS", justify="right")
    table.add_column("INP", justify="right")

    for result in audit_results:
        metrics = result.metrics
        title = escape(result.title) if result.title else "[dim]—[/dim]"
        missing_alt = (
            f"[red]{result.images_without_alt}[/red]"
            if result.images_without_alt > 0
            else "[green]0[/green]"
        )
        table.add_row(
            escape(result.url),
            _format_status_code(result.status_code),
            title,
            missing_alt,
            _format_metric(metrics.lcp_ms, 2500, 4000),
            _format_metric(metrics.cls, 0.1, 0.25, unit="", precision=3),
            _format_metric(metrics.inp_ms, 200, 500),
        )

    console.print(table)

    for result in audit_results:
        issues = [
            f"[bold red]ERR[/bold red] - {escape(error)}"
            for error in result.errors
        ]
        issues.extend(
            f"[bold yellow]WRN[/bold yellow] - {escape(warning)}"
            for warning in result.warnings
        )
        if issues:
            error_console.print(
                Panel(
                    "\n".join(issues),
                    title=f"[bold]{escape(result.url)}[/bold]",
                    border_style="red",
                )
            )


def save_json(results: Sequence[AuditItem], output_path: Path) -> None:
    """Write normalized audit results as indented UTF-8 JSON."""
    audit_results = list(_iter_normalized(results))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(
        _AUDIT_RESULTS_ADAPTER.dump_json(audit_results, indent=2) + b"\n"
    )
