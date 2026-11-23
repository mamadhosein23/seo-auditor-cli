from __future__ import annotations

from pathlib import Path
from typing import Seq
    precision: int = 0,
) -> str:
    """Format Web Vitals using standard Google thresholds."""
    if value is None:tus_code),
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
