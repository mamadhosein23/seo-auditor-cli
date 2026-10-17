# SEO Auditor CLI

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/playwright-chromium-green.svg)](https://playwright.dev/python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A high-performance CLI tool for preliminary on-page SEO analysis and Core Web Vitals auditing powered by Headless Chromium and Playwright.

---

## Features

- **Metadata Inspection:** Extracts `<title>`, meta description, canonical tags, Open Graph (OG), and JSON-LD schemas.
- **Document Structure:** Audits semantic HTML hierarchy, heading distributions (`H1`-`H6`), and inline content health.
- **Accessibility & Media:** Detects missing `alt` attributes and unoptimized asset declarations.
- **Performance Metrics:** Measures approximate real-time **LCP** (Largest Contentful Paint) and **CLS** (Cumulative Layout Shift).
- **Concurrent Audits:** Asynchronously scans multiple URLs with configurable concurrency limits.
- **Structured Export:** Generates clean, machine-readable JSON reports.

---

## Installation

Ensure you have **Python 3.10+** installed.

1. **Clone the repository:**
```bash
   git clone https://github.com/mamadhosein23/seo-auditor-cli.git
   cd seo-auditor-cli
   
