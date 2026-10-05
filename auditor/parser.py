from typing import Any

from playwright.async_api import Page
from pydantic import BaseModel, Field

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
  const getMeta = (selector) => {
    const el = document.querySelector(selector);
    return el ? el.getAttribute("content")?.trim() || null : null;
  };

  // 1. Heading Counts (h1 to h6)
  const headingCounts = {};
  for (let level = 1; level <= 6; level++) {
    headingCounts[`h${level}`] = document.querySelectorAll(`h${level}`).length;
  }

  // 2. Semantic Elements
  const semanticTags = ["main", "nav", "header", "footer", "article", "section", "aside"];
  const semanticElements = {};
  for (const tag of semanticTags) {
    semanticElements[tag] = document.querySelectorAll(tag).length;
  }

  // 3. OpenGraph Tags (پشتیبانی از هر دو اتریبیوت استاندارد property و name)
  const openGraph = {};
  const ogElements = document.querySelectorAll('meta[property^="og:"], meta[name^="og:"]');
  for (const el of ogElements) {
    const key = el.getAttribute("property") || el.getAttribute("name");
    const value = el.getAttribute("content")?.trim();
    if (key && value) {
      openGraph[key.toLowerCase()] = value;
    }
  }

  // 4. Schema.org JSON-LD extraction
  const schemaOrg = [];
  let invalidSchemaCount = 0;
  for (const script of document.querySelectorAll('script[type="application/ld+json"]')) {
    const text = script.textContent?.trim();
    if (!text) continue;
    try {
      schemaOrg.push(JSON.parse(text));
    } catch (_) {
      invalidSchemaCount++;
    }
  }

  // 5. بررسی تصاویر فاقد alt (حذف تگ‌های با alt فاقد متن یا خالی از whitespace)
  let imagesWithoutAlt = 0;
  for (const img of document.querySelectorAll("img")) {
    if (!img.hasAttribute("alt") || img.getAttribute("alt").trim() === "") {
      imagesWithoutAlt++;
    }
  }

  // 6. استخراج Canonical با URL Absolute
  const canonicalEl = document.querySelector('link[rel="canonical"]');
  let canonical = null;
  if (canonicalEl) {
    canonical = canonicalEl.href || canonicalEl.getAttribute("href") || null;
  }

  return {
    final_url: window.location.href,
    title: document.title ? document.title.trim() : null,
    meta_description: getMeta('meta[name="description" i]'),
    canonical: canonical,
    lang: document.documentElement.getAttribute("lang")?.trim() || null,
    heading_counts: headingCounts,
    semantic_elements: semanticElements,
    open_graph: openGraph,
    schema_org: schemaOrg,
    images_without_alt: imagesWithoutAlt,
    invalid_schema_count: invalidSchemaCount
  };
}
"""


async def parse_page(
    page: Page,
    requested_url: str,
    status_code: int | None,
    metrics: WebMetrics | None = None,
) -> AuditResult:
    data = await page.evaluate(PARSER_SCRIPT)

    warnings: list[str] = []
    if data["invalid_schema_count"] > 0:
        warnings.append(f"{data['invalid_schema_count']} بلوک JSON-LD نامعتبر پیدا شد.")

    if not data["title"]:
        warnings.append("تگ <title> در صفحه یافت نشد.")

    if not data["meta_description"]:
        warnings.append("تگ meta description یافت نشد.")

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
        metrics=metrics or WebMetrics(),
        warnings=warnings,
    )
