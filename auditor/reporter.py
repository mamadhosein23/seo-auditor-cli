from pathlib import Path
from typing import Sequence

from pydantic import TypeAdapter
from rich.console import Console
from rich.table import Table

from auditor.parser import AuditResult

console = Console()
error_console = Console(stderr=True)

# Performance optimization: Module-level TypeAdapter avoids reconstructing the schema
_AUDIT_RESULTS_ADAPTER: TypeAdapter[list[AuditResult]] = TypeAdapter(list[AuditResult])


def _format_metric(
    value: float | None,
    good_threshold: float,
    poor_threshold: float,
    unit: str = " ms",
    precision: int = 0,
) -> str:
    """Format Web Vitals metrics according to Google's official thresholds."""
    if value is None:
        return "[dim]—[/dim]"
    color = "green" if value <= good_threshold else "yellow" if value <= poor_threshold else "red"
    return f"[{color}]{value:.{precision}f}{unit}[/{color}]"


def _format_status_code(code: int | None) -> str:
    """Colorize HTTP status codes based on standard response ranges."""
    if code is None:
        return "[dim]—[/dim]"
    if 200 <= code < 300:
        return f"[green]{code}[/green]"
    if 300 <= code < 400:
        return f"[yellow]{code}[/yellow]"
    if 400 <= code < 600:
        return f"[red]{code}[/red]"
    return f"[white]{code}[/white]"


def print_report(results: Sequence[AuditResult]) -> None:
    """Render structured tabular report to stdout and warnings/errors to stderr."""
    table = Table(title="SEO & Performance Audit", header_style="bold cyan")

    table.add_column("URL", overflow="fold", no_wrap=False)
    table.add_column("HTTP", justify="right")
    table.add_column("Title", overflow="ellipsis", max_width=40)
    table.add_column("LCP", justify="right")
    table.add_column("CLS", justify="right")
    table.add_column("INP", justify="right")

    for result in results:
        metrics = result.metrics
        lcp = metrics.lcp_ms if metrics else None
        cls = metrics.cls if metrics else None
        inp = metrics.inp_ms if metrics else None

        table.add_row(
            result.url,
            _format_status_code(result.status_code),
            result.title or "[dim]—[/dim]",
            _format_metric(lcp, 2500, 4000),
            _format_metric(cls, 0.1, 0.25, unit="", precision=3),
            _format_metric(inp, 200, 500),
        )

    console.print(table)

    # Route errors and warnings distinctly to stderr
    for result in results:
        for error in result.errors:
            error_console.print(f"[bold red]ERROR[/bold red]   — {result.url}: {error}")
        for warning in result.warnings:
            error_console.print(f"[bold yellow]WARNING[/bold yellow] — {result.url}: {warning}")


def save_json(results: Sequence[AuditResult], output_path: Path) -> None:
    """Serialize results list to an indented JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_bytes = _AUDIT_RESULTS_ADAPTER.dump_json(list(results), indent=2)
    output_path.write_bytes(json_bytes + b"\n")
