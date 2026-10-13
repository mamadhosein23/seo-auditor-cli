from typing import Any

from playwright.async_api import Page
from pydantic import BaseModel, Field

from auditor.metrics import WebMetrics


class AuditResult(BaseModel):
    """Structured output of a single-page SEO + basic performance audit."""

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

  // Heading counts (H1..H6)
  const headingCounts = {};
  for (let level = 1; level <= 6; level++) {
    headingCounts[`h${level}`] =
      document.querySelectorAll(`h${level}`).length;
  }

  // Semantic element counts
  const semanticTags = [
    "main", "nav", "header", "footer", "article", "section", "aside"
  ];
  const semanticElements = {};
  for (const tag of semanticTags) {
    semanticElements[tag] = document.querySelectorAll(tag).length;
  }

  // Open Graph tags
  const openGraph = {};
  const ogElements = document.querySelectorAll(
    'meta[property^="og:" i], meta[name^="og:" i]'
  );

  for (const el of ogElements) {
    const key = el.getAttribute("property") || el.getAttribute("name");
    const value = el.getAttribute("content")?.trim();

    if (key && value) {
      openGraph[key.toLowerCase()] = value;
    }
  }

  // JSON-LD blocks; accept case variations and MIME parameters.
  const schemaOrg = [];
  let invalidSchemaCount = 0;

  const jsonLdScripts = [...document.querySelectorAll("script[type]")].filter(
    (script) => {
      const mimeType = (script.getAttribute("type") || "")
        .split(";")[0]
        .trim()
        .toLowerCase();

      return mimeType === "application/ld+json";
    }
  );

  for (const script of jsonLdScripts) {
    const text = script.textContent?.trim();
    if (!text) continue;

    try {
      schemaOrg.push(JSON.parse(text));
    } catch (_) {
      invalidSchemaCount++;
    }
  }

  // An absent alt attribute is different from alt="":
  // an empty alt can be correct for a decorative image.
  let imagesWithoutAlt = 0;
  for (const img of document.querySelectorAll("img")) {
    if (!img.hasAttribute("alt")) {
      imagesWithoutAlt++;
    }
  }

  // Resolve the first canonical URL against the document base URL.
  // Do not use the reflected .href for an empty attribute: it can resolve
  // to the current page URL and look like a valid canonical.
  const canonicalLinks = document.querySelectorAll(
    'link[rel~="canonical" i]'
  );

  let canonical = null;
  let invalidCanonical = false;

  if (canonicalLinks.length > 0) {
    const rawHref = canonicalLinks[0].getAttribute("href")?.trim();

    if (rawHref) {
      try {
        canonical = new URL(rawHref, document.baseURI).href;
      } catch (_) {
        invalidCanonical = true;
      }
    } else {
      invalidCanonical = true;
    }
  }

  return {
    final_url: window.location.href,
    title: document.title?.trim() || null,
    meta_description: getMeta('meta[name="description" i]'),
    canonical,
    canonical_count: canonicalLinks.length,
    invalid_canonical: invalidCanonical,
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
    """Parse on-page SEO signals from the current DOM and return an AuditResult."""
    data = await page.evaluate(PARSER_SCRIPT)

    if not isinstance(data, dict):
        raise RuntimeError("Page parser did not return the expected data.")

    warnings: list[str] = []

    if data["invalid_schema_count"] > 0:
        warnings.append(
            f"Found {data['invalid_schema_count']} invalid JSON-LD block(s)."
        )

    if not data["title"]:
        warnings.append("Missing <title> tag.")

    if not data["meta_description"]:
        warnings.append("Missing meta description tag.")

    if data["canonical_count"] > 1:
        warnings.append(
            f"Found {data['canonical_count']} canonical link elements."
        )

    if data["invalid_canonical"]:
        warnings.append("Canonical link has a missing or invalid href.")

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
        metrics=metrics if metrics is not None else WebMetrics(),
        warnings=warnings,
    )
