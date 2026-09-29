from typing import Any

from pydantic import BaseModel, Field
from playwright.async_api import Page

from auditor.metrics import WebMetrics


class AuditResult(BaseModel):
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
() => {
  const content = (selector) => {
    const element = document.querySelector(selector);
    const value = element?.content?.trim();
    return value || null;
  };

  const headingCounts = {};
  for (let level = 1; level <= 6; level++) {
    headingCounts[`h${level}`] =
      document.querySelectorAll(`h${level}`).length;
  }

  const semanticTags = [
    "main", "nav", "header", "footer",
    "article", "section", "aside"
  ];

  const semanticElements = {};
  for (const tag of semanticTags) {
    semanticElements[tag] = document.querySelectorAll(tag).length;
  }

  const openGraph = {};
  for (const element of document.querySelectorAll('meta[property^="og:"]')) {
    const key = element.getAttribute("property");
    const value = element.getAttribute("content")?.trim();
    if (key && value) openGraph[key] = value;
  }

  const schemaOrg = [];
  let invalidSchemaCount = 0;

  for (const script of document.querySelectorAll(
    'script[type="application/ld+json"]'
  )) {
    try {
      schemaOrg.push(JSON.parse(script.textContent || ""));
    } catch (_) {
      invalidSchemaCount++;
    }
  }

  return {
    final_url: location.href,
    title: document.title.trim() || null,
    meta_description: content('meta[name="description" i]'),
    canonical: document.querySelector('link[rel="canonical"]')?.href || null,
    lang: document.documentElement.lang || null,
    heading_counts: headingCounts,
    semantic_elements: semanticElements,
    open_graph: openGraph,
    schema_org: schemaOrg,
    images_without_alt: document.querySelectorAll("img:not([alt])").length,
    invalid_schema_count: invalidSchemaCount
  };
}
"""


async def parse_page(
    page: Page,
    requested_url: str,
    status_code: int | None,
) -> AuditResult:
    data = await page.evaluate(PARSER_SCRIPT)

    warnings = []
    if data["invalid_schema_count"]:
        warnings.append(
            f'{data["invalid_schema_count"]} بلوک JSON-LD نامعتبر پیدا شد.'
        )

    return AuditResult(
        url=requested_url,
        final_url=data["final_url"],
        status_code=status_code,
        title=data["title"],
        meta_description=data["meta_description"],
        canonical=data["canonical"],
        lang=data["lang"],
        heading_counts=data["heading_counts"],
        semantic_elements=data["semantic_elements"],
        open_graph=data["open_graph"],
        schema_org=data["schema_org"],
        images_without_alt=data["images_without_alt"],
        warnings=warnings,
    )
