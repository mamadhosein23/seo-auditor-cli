from __future__ import annotations

from typing import Any

from playwright.async_api import Page
from pydantic import BaseModel, Field

from auditor.metrics import WebMetrics, collect_metrics


class AuditResult(BaseModel):
    """Structured output of a single-page SEO and performance audit."""

    url: str
    final_url: str | None = None
    status_code: int | None = None
    title: str | None = None
    meta_description: str | None = None
    canonical: str | None = None
    lang: str | None = None
    heading_counts: dict[str, int] = Field(default_factory=dict)
    semantic_elements: dict[str, int] = Field(default_factory=dict)
    open_graph: dict[str, str] = Field(default_factory=dict)
    schema_org: list[Any] = Field(default_factory=list)
    images_without_alt: int = 0
    metrics: WebMetrics = Field(default_factory=WebMetrics)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


PARSER_SCRIPT = r"""
(() => {
  const doc = document;

  const headingCounts = Object.fromEntries(
    [1, 2, 3, 4, 5, 6].map((level) => [
      `h${level}`,
      doc.querySelectorAll(`h${level}`).length
    ])
  );

  const semanticElements = Object.fromEntries(
    ["main", "nav", "header", "footer", "article", "section", "aside"].map(
      (tag) => [tag, doc.querySelectorAll(tag).length]
    )
  );

  const openGraph = {};
  doc
    .querySelectorAll('meta[property^="og:" i], meta[name^="og:" i]')
    .forEach((element) => {
      const key = (
        element.getAttribute("property") ||
        element.getAttribute("name") ||
        ""
      ).toLowerCase();
      const value = element.getAttribute("content");

      if (key && value?.trim()) {
        openGraph[key] = value.trim();
      }
    });

  const schemaOrg = [];
  let invalidSchemaCount = 0;

  doc.querySelectorAll('script[type="application/ld+json"]').forEach((script) => {
    const text = script.textContent?.trim();

    if (!text) return;

    try {
      schemaOrg.push(JSON.parse(text));
    } catch {
      invalidSchemaCount += 1;
    }
  });

  const canonicalLinks = doc.querySelectorAll(
    'link[rel~="canonical" i]'
  );
  let canonical = null;
  let invalidCanonical = false;

  if (canonicalLinks.length > 0) {
    const href = canonicalLinks[0].getAttribute("href");

    if (!href?.trim()) {
      invalidCanonical = true;
    } else {
      try {
        canonical = new URL(href, doc.baseURI).href;
      } catch {
        invalidCanonical = true;
      }
    }
  }

  return {
    final_url: window.location.href,
    title: doc.title?.trim() || null,
    meta_description:
      doc.querySelector('meta[name="description" i]')
        ?.getAttribute("content")
        ?.trim() || null,
    canonical,
    canonical_count: canonicalLinks.length,
    invalid_canonical: invalidCanonical,
    lang: doc.documentElement.getAttribute("lang")?.trim() || null,
    heading_counts: headingCounts,
    semantic_elements: semanticElements,
    open_graph: openGraph,
    schema_org: schemaOrg,
    images_without_alt: [...doc.querySelectorAll("img")].filter(
      (image) => !image.hasAttribute("alt")
    ).length,
    invalid_schema_count: invalidSchemaCount
  };
})()
"""


async def parse_page(
    page: Page,
    requested_url: str,
    status_code: int | None,
    metrics: WebMetrics | None = None,
) -> AuditResult:
    """Parse on-page SEO signals and compile an AuditResult."""
    data: object = await page.evaluate(PARSER_SCRIPT)

    if not isinstance(data, dict):
        raise RuntimeError("Failed to retrieve data from page parser.")

    warnings: list[str] = []

    invalid_schema_count = data.get("invalid_schema_count", 0)
    if isinstance(invalid_schema_count, int) and invalid_schema_count > 0:
        warnings.append(
            f"Found {invalid_schema_count} invalid JSON-LD block(s)."
        )

    if not data.get("title"):
        warnings.append("Missing <title> tag.")

    if not data.get("meta_description"):
        warnings.append("Missing meta description.")

    canonical_count = data.get("canonical_count", 0)
    if isinstance(canonical_count, int) and canonical_count > 1:
        warnings.append("Multiple canonical links detected.")

    if data.get("invalid_canonical"):
        warnings.append("Canonical link is malformed or missing href.")

    collected_metrics = metrics if metrics is not None else await collect_metrics(page)

    return AuditResult(
        url=requested_url,
        final_url=data.get("final_url"),
        status_code=status_code,
        title=data.get("title"),
        meta_description=data.get("meta_description"),
        canonical=data.get("canonical"),
        lang=data.get("lang"),
        heading_counts=data.get("heading_counts") or {},
        semantic_elements=data.get("semantic_elements") or {},
        open_graph=data.get("open_graph") or {},
        schema_org=data.get("schema_org") or [],
        images_without_alt=data.get("images_without_alt", 0),
        metrics=collected_metrics,
        warnings=warnings,
    )
