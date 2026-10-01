# SEO Auditor CLI

A CLI tool for preliminary SEO analysis and web performance auditing using Chromium and Playwright.

## Features

- Extract page title, meta description, and canonical tags.
- Count headings and semantic HTML elements.
- Extract Open Graph and JSON-LD metadata.
- Count images missing `alt` attributes.
- Measure approximate LCP and CLS during the visit.
- Save reports in JSON format.
- Audit multiple URLs with limited concurrency.

## Installation

Python 3.10 or higher is required.
```bash
python -m venv .venv
