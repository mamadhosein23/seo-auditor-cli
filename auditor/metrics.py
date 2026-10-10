from pydantic import BaseModel, Field
from playwright.async_api import Page


class WebMetrics(BaseModel):
    """Browser-side performance measurements collected in-page (not lab CWV)."""

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
    clsSessionStart: 0,
    clsLastShift: 0,
    interactions: {}
  };

  // Expose state on window so Playwright can read it later.
  window.__seoAuditMetrics = state;

  // LCP
  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        state.lcp = entry.startTime;
      }
    });
    observer.observe({ type: "largest-contentful-paint", buffered: true });
  } catch (_) {}

  // CLS (session windowing per web-vitals approach)
  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.hadRecentInput) continue;

        const now = entry.startTime;
        const sessionExpired =
          state.clsSessionStart === 0 ||
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
  } catch (_) {}

  // INP approximation via Event Timing API (interactionId aggregation)
  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.interactionId || entry.interactionId === 0) continue;

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
  } catch (_) {}
})();
"""


async def collect_metrics(page: Page) -> WebMetrics:
    """Read metrics collected by the injected init script."""
    data = await page.evaluate(
        """() => {
          const state = window.__seoAuditMetrics;
          if (!state) return null;

          const toFiniteOrNull = (v) =>
            Number.isFinite(v) ? v : null;

          const interactions = Object.values(state.interactions || {})
            .filter((value) => Number.isFinite(value))
            .sort((a, b) => a - b);

          // Approximate p98; with a small sample size this often equals
          // the longest observed interaction in this session.
          const index = interactions.length
            ? Math.max(0, Math.ceil(interactions.length * 0.98) - 1)
            : -1;

          return {
            lcp_ms: toFiniteOrNull(state.lcp),
            cls: toFiniteOrNull(state.cls),
            inp_ms: index >= 0 ? toFiniteOrNull(interactions[index]) : null
          };
        }"""
    )

    if not data:
        return WebMetrics(notes=["In-page metrics collection did not initialize."])

    notes = [
        "INP is approximated only from interactions observed during this single run; "
        "if no interactions occur, INP will be null."
    ]

    return WebMetrics(
        lcp_ms=data.get("lcp_ms"),
        cls=data.get("cls"),
        inp_ms=data.get("inp_ms"),
        notes=notes,
    )
