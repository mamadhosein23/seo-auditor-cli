import json
from pathlib import Path
from typing import Sequence

from rich.console import Console
from rich.table import Table

from auditor.parser import AuditResult


console = Console()


def _format_ms(value: float | None) -> str:
    return f"{value:.0f} ms" if value is not None else "—"


def _format_cls(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else "—"


def print_report(results: Sequence[AuditResult]) -> None:
    table = Table(title="SEO & Performance Audit")

    table.add_column("URL", overflow="fold")
    table.add_column("HTTP", justify="right")
    table.add_column("Title")
    table.add_column("LCP")
    table.add_column("CLS")
    table.add_column("INP")

    for result in results:
        table.add_row(
            result.url,
            str(result.status_code) if result.status_code is not None else "—",
            result.title or "—",
            _format_ms(result.metrics.lcp_ms),
            _format_cls(result.metrics.cls),
            _format_ms(result.metrics.inp_ms),
        )

    console.print(table)

    for result in results:
        for error in result.errors:
            console.print(f"[red]خطا — {result.url}: {error}[/red]")
        for warning in result.warnings:
            console.print(f"[yellow]هشدار — {result.url}: {warning}[/yellow]")


def save_json(results: Sequence[AuditResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = [result.model_dump(mode="json") for result in results]
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
