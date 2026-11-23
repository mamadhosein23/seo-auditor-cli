from __future__ import annotations

from pathlib import Path
from typing import Seq
    precision: int = 0,
) -> str:
    """Format Web Vitals using standard Google thresholds."""
    audit_results = list(_iter_normalized(results))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(_AUDIT_RESULTS_ADAPTER.dump_json(audit_results, indent=2) + b"\n")
