from __future__ import annotations

from math import isfinite

from pydantic import BaseModel, ConfigDict, Field
from playwright.async_api import Page


class WebMetrics(BaseModel):
    """Approximate browser-side Core Web Vitals measurements."""

    model_config = ConfigDict(extra="forbid")

    lcp_ms: float | None = None
    cls: float | None = None
    inp_ms: float | None = None
    notes: list[str] = Field(default_factory=list)


def _finite_number(value: object) -> float | None:
    """Return a finite numeric value, excluding booleans."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None

    number = float(value)
    return number if isfinite(number) else None


async def collect_metrics(page: Page) -> WebMetrics:
    """Read metrics collected by the injected browser-side script."""
    try:
        data: object = await page.evaluate(_COLLECT_METRICS_SCRIPT)
    except Exception as exc:
        return WebMetrics(
            notes=[f"Unable to read in-page metrics: {type(exc).__name__}: {exc}"]
        )

    if not isinstance(data, dict):
        return WebMetrics(
            notes=["In-page metrics collection script did not initialize."]
        )

    lcp_ms = _finite_number(data.get("lcp_ms"))
    cls = _finite_number(data.get("cls"))
    inp_ms = _finite_number(data.get("inp_ms"))

    interaction_count = data.get("interaction_count")
    has_interactions = (
        isinstance(interaction_count, int)
        and not isinstance(interaction_count, bool)
        and interaction_count > 0
    )

    notes: list[str] = []

    if not has_interactions:
        notes.append(
            "INP is unavailable because no qualifying user interactions were observed."
        )
    else:
        notes.append(
            "INP is approximate: the standard INP percentile and outlier "
            "adjustment are not implemented."
        )

    if lcp_ms is None:
        notes.append("LCP is unavailable or was not observed.")

    if cls is None:
        notes.append("CLS is unavailable or was not observed.")

    return WebMetrics(
        lcp_ms=lcp_ms,
        cls=cls,
        inp_ms=inp_ms,
        notes=notes,
    )
