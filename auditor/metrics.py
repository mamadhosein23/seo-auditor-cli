from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from playwright.async_api import Page


class WebMetrics(BaseModel):
    """Approximate browser-side Core Web Vitals measurements."""

    model_config = ConfigDict(extra="forbid")

    lcp_ms: float | None = None
    cls: float | None = None
    inp_ms: float | None = None
    notes: list[str] = Field(default_factory=list)


METRICS_INIT_SCRIPT = r"""
(() => {
  const state = {
    lcp: null,
    cls: 0,
    clsSessionValue: 0,
    clsSessionStart: null,
    clsLastShift: null,
    interactions: Object.create(null)
  };

  Object.defineProperty(window, "__seoAuditMetrics", {
    value: state,
    configurable: false,
    enumerable: false,
    writable: false
  });

  const supports = (type) =>
    PerformanceObserver.supportedEntryTypes?.includes(type) ?? false;

  // Largest Contentful Paint
  if (supports("largest-contentful-paint")) {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          state.lcp = entry.renderTime || entry.loadTime || entry.startTime;
        }
      });

      observer.observe({
        type: "largest-contentful-paint",
        buffered: true
      });
    } catch (_) {
      // Keep the rest of the metrics available if this observer is unsupported.
    }
  }

  // Cumulative Layout Shift using session windows.
  if (supports("layout-shift")) {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.hadRecentInput) continue;

          const now = entry.startTime;
          const sessionExpired =
            state.clsSessionStart === null ||
            now - state.clsLastShift > 1000 ||
            now - state.clsSessionStart > 5000;

          if (sessionExpired) {
            state.clsSessionStart = now;
            state.clsSessionValue = entry.value;
          } else {
            state.clsSessionValue += entry.value;
          }

          state.clsLastShift = now;
          state.cls = Math.max(state.cls, state.clsSessionValue);
        }
      });

      observer.observe({ type: "layout-shift", buffered: true });
    } catch (_) {
      // Keep the rest of the metrics available if this observer is unsupported.
    }
  }

  // Event Timing entries used to approximate Interaction to Next Paint.
  if (supports("event")) {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!entry.interactionId) continue;

          const id = String(entry.interactionId);
          state.interactions[id] = Math.max(
            state.interactions[id] || 0,
            entry.duration
          );
        }
      });

      observer.observe({
        type: "event",
        buffered: true,
        durationThreshold: 16
      });
    } catch (_) {
      // Keep the rest of the metrics available if this observer is unsupported.
    }
  }
})();
"""


_COLLECT_METRICS_SCRIPT = r"""
() => {
  const state = window.__seoAuditMetrics;
  if (!state) return null;

  const toFiniteOrNull = (value) =>
    typeof value === "number" && Number.isFinite(value)
      ? Math.round(value * 1000) / 1000
      : null;

  const interactions = Object.values(state.interactions || {})
    .filter((value) => typeof value === "number" && Number.isFinite(value))
    .sort((a, b) => a - b);

  // This is an approximation; see the Python-side notes for limitations.
  let inp = null;
  if (interactions.length > 0) {
    const index = Math.max(0, Math.ceil(interactions.length * 0.98) - 1);
    inp = interactions[index];
  }

  return {
    lcp_ms: toFiniteOrNull(state.lcp),
    cls: toFiniteOrNull(state.cls),
    inp_ms: toFiniteOrNull(inp),
    interaction_count: interactions.length
  };
}
"""


async def collect_metrics(page: Page) -> WebMetrics:
    """Read metrics collected by the injected browser-side script."""
    try:
        data: Any = await page.evaluate(_COLLECT_METRICS_SCRIPT)
    except Exception as exc:
        return WebMetrics(
            notes=[f"Unable to read in-page metrics: {type(exc).__name__}: {exc}"]
        )

    if not isinstance(data, dict):
        return WebMetrics(
            notes=["In-page metrics collection script did not initialize."]
        )

    notes: list[str] = []

    interaction_count = data.get("interaction_count")
    if not isinstance(interaction_count, int) or interaction_count == 0:
        notes.append(
            "INP is unavailable because no qualifying user interactions were observed."
        )
    else:
        notes.append(
            "INP is an approximation; the standard INP percentile/outlier "
            "handling is not implemented."
        )

    return WebMetrics(
        lcp_ms=data.get("lcp_ms"),
        cls=data.get("cls"),
        inp_ms=data.get("inp_ms"),
        notes=notes,
    )
