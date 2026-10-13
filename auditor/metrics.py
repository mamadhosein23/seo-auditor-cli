from pydantic import BaseModel, Field
from playwright.async_api import Page


class WebMetrics(BaseModel):
    """Browser-side performance measurements collected in-page (Core Web Vitals approximation)."""

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
    interactions: {}
  };

  window.__seoAuditMetrics = state;

  // 1. Largest Contentful Paint (LCP)
  if (PerformanceObserver.supportedEntryTypes?.includes("largest-contentful-paint")) {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        if (entries.length > 0) {
          // The last observed entry prior to user interaction is the actual LCP
          const lastEntry = entries[entries.length - 1];
          state.lcp = lastEntry.renderTime || lastEntry.loadTime || lastEntry.startTime;
        }
      });
      observer.observe({ type: "largest-contentful-paint", buffered: true });
    } catch (_) {}
  }

  // 2. Cumulative Layout Shift (CLS) - Official Session Windowing (Max 5s window, 1s gap)
  if (PerformanceObserver.supportedEntryTypes?.includes("layout-shift")) {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          // Ignore shifts caused immediately by direct user actions
          if (entry.hadRecentInput) continue;

          const now = entry.startTime;

          // A new session window starts if:
          // - No shift has occurred yet
          // - More than 1 second has elapsed since the last shift
          // - The current window has lasted longer than 5 seconds
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
    } catch (_) {}
  }

  // 3. Interaction to Next Paint (INP) - Event Timing API
  if (PerformanceObserver.supportedEntryTypes?.includes("event")) {
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
    } catch (_) {}
  }
})();
"""


async def collect_metrics(page: Page) -> WebMetrics:
    """Read metrics collected by the injected init script."""
    data = await page.evaluate(
        """() => {
          const state = window.__seoAuditMetrics;
          if (!state) return null;

          const toFiniteOrNull = (v) =>
            typeof v === "number" && Number.isFinite(v) ? Math.round(v * 1000) / 1000 : null;

          const interactions = Object.values(state.interactions || {})
            .filter((value) => typeof value === "number" && Number.isFinite(value))
            .sort((a, b) => a - b);

          // Google definition: p98 interaction duration for sites with many interactions,
          // or max interaction duration if total count < 50.
          let inp = null;
          if (interactions.length > 0) {
            const index = Math.max(0, Math.ceil(interactions.length * 0.98) - 1);
            inp = interactions[index];
          }

          return {
            lcp_ms: toFiniteOrNull(state.lcp),
            cls: toFiniteOrNull(state.cls),
            inp_ms: toFiniteOrNull(inp)
          };
        }"""
    )

    if not data:
        return WebMetrics(notes=["In-page metrics collection script did not initialize."])

    notes: list[str] = []
    if data.get("inp_ms") is None:
        notes.append(
            "INP is null because automated crawler runs do not trigger real user input interactions."
        )

    return WebMetrics(
        lcp_ms=data.get("lcp_ms"),
        cls=data.get("cls"),
        inp_ms=data.get("inp_ms"),
        notes=notes,
    )
