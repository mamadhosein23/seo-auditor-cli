from __future__ import annotations

from typing import Any
from playwright.async_api import Page
from pydantic import BaseModel, Field

from auditor.metrics import WebMetrics

class AuditResult(BaseModel):
    """Structured output of a single-page SEO + performance audit."""
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
    warnings: list[str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=dict)

# Optimized JavaScript parser for better performance and safety
PARSER_SCRIPT = r"""
(() => {
    const safeGet = (fn) => { try { return fn(); } catch (e) { return null; } };
    
    const doc = document;
    const headingCounts = Object.fromEntries(
        [1, 2, 3, 4, 5, 6].map(i => [`h${i}`, doc.querySelectorAll(`h${i}`).length])
    );
    
    const semanticElements = Object.fromEntries(
        ['main', 'nav', 'header', 'footer', 'article', 'section', 'aside'].map(tag => [tag, doc.querySelectorAll(tag).length])
    );

    const openGraph = {};
    doc.querySelectorAll('meta[property^="og:" i], meta[name^="og:" i]').forEach(el => {
        const key = (el.getAttribute('property') || el.getAttribute('name')).toLowerCase();
        const val = el.getAttribute('content');
        if (key && val) openGraph[key] = val.trim();
    });

    const schemaOrg = [];
    let invalidSchemaCount = 0;
    doc.querySelectorAll('script[type="application/ld+json"]').forEach(script => {
        try {
            if (script.textContent.trim()) schemaOrg.push(JSON.parse(script.textContent));
        } catch { invalidSchemaCount++; }
    });

    const canonicalLinks = doc.querySelectorAll('link[rel~="canonical" i]');
    let canonical = null;
    let invalidCanonical = false;
    if (canonicalLinks.length > 0) {
        const href = canonicalLinks[0].getAttribute('href');
        if (!href) invalidCanonical = true;
        else canonical = safeGet(() => new URL(href, doc.baseURI).href);
    }

    return {
        final_url: window.location.href,
        title: doc.title?.trim() || null,
        meta_description: doc.querySelector('meta[name="description" i]')?.getAttribute('content')?.trim() || null,
        canonical,
        canonical_count: canonicalLinks.length,
        invalid_canonical: invalidCanonical,
        lang: doc.documentElement.getAttribute('lang')?.trim() || null,
        heading_counts: headingCounts,
        semantic_elements: semanticElements,
        open_graph: openGraph,
        schema_org: schemaOrg,
        images_without_alt: [...doc.querySelectorAll('img')].filter(img => !img.hasAttribute('alt')).length,
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
    data = await page.evaluate(PARSER_SCRIPT)
    
    if not isinstance(data, dict):
        raise RuntimeError("Failed to retrieve data from page parser.")

    warnings = []
    if data["invalid_schema_count"] > 0:
        warnings.append(f"Found {data['invalid_schema_count']} invalid JSON-LD block(s).")
    if not data["title"]: warnings.append("Missing <title> tag.")
    if not data["meta_description"]: warnings.append("Missing meta description.")
    if data["canonical_count"] > 1: warnings.append("Multiple canonical links detected.")
    if data["invalid_canonical"]: warnings.append("Canonical link is malformed or missing href.")

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
        warnings=warnings
    )
