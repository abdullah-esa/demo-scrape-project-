# 🕷️ Config-Driven Web Scraping & Data Cleaning Framework

A **modular, production-ready, configuration-driven** web scraping framework in Python. Point it at a new site by editing a single config file — **zero code changes required** anywhere else.

Built around four clean layers:

| Layer | File | Responsibility |
|---|---|---|
| **Config** | `config.py` | Declare target sites, selectors, cleaning rules |
| **Scrape** | `scraper.py` | HTTP session, retries, rate-limiting, generic extraction |
| **Clean** | `cleaner.py` | Pandas pipeline: dtype casting, strip patterns, dedupe |
| **Export** | `exporter.py` | CSV + JSON output with logging and dir creation |

An orchestration entry point (`main.py`) wires them together via a CLI.

---

## 📖 Table of Contents

1. [Features](#-features)
2. [Project Structure](#-project-structure)
3. [Prerequisites](#-prerequisites)
4. [Installation](#-installation)
5. [Quick Start](#-quick-start)
6. [Configuration Reference](#-configuration-reference)
7. [Adding a New Target Site](#-adding-a-new-target-site)
8. [CLI Reference](#-cli-reference)
9. [Output Format](#-output-format)
10. [How It Works (Architecture)](#-how-it-works-architecture)
11. [Extending the Framework](#-extending-the-framework)
12. [Troubleshooting](#-troubleshooting)
13. [Best Practices & Legal Notes](#-best-practices--legal-notes)
14. [FAQ](#-faq)

---

## ✨ Features

- **Configuration-driven** — new site = new `SiteConfig` entry. No code edits.
- **Robust HTTP layer** — `requests.Session`, custom UA, retries with exponential backoff, timeout handling, graceful failure.
- **Polite scraping** — configurable rate limit + random jitter between requests.
- **Generic extraction engine** — CSS selector field-mapping; safe helpers return `None` instead of raising `AttributeError`.
- **Attribute + text extraction** — grab `href`, `src`, or any attribute, not just inner text.
- **Relative URL resolution** — automatically resolves `href`/`src` against the current page.
- **Pagination support** — follows "next page" links up to `max_pages`.
- **Pandas cleaning pipeline** — dtype casting (`int`, `float`, `datetime`, `str`), regex strip patterns, dedupe on primary keys, null handling.
- **Dual export** — CSV (UTF-8 BOM for Excel) + pretty JSON, in `output/`.
- **Structured logging** — every stage logged with timestamps and levels.
- **CLI entry point** — `python main.py --site <name>`.

---

## 📁 Project Structure

```
scraper/
├── config.py          # Site configurations (SiteConfig + SITES registry)
├── scraper.py         # HttpClient + extraction engine
├── cleaner.py         # Pandas cleaning pipeline
├── exporter.py        # CSV/JSON export
├── main.py            # CLI orchestrator
├── requirements.txt   # Dependencies
├── .gitignore
├── README.md
└── output/            # Auto-created at runtime (git-ignored)
    ├── books_toscrape.csv
    └── books_toscrape.json
```

---

## 🔧 Prerequisites

- **Python** ≥ 3.9 (tested on 3.11)
- **Conda** (recommended) or `pip`
- **Git** (for version control)
- Network access to the target site

---

## 🚀 Installation

### Option A — Conda (recommended)

```bash
# 1. Create a dedicated environment
conda create -n scraper python=3.11 -y

# 2. Activate
conda activate scraper

# 3. Install dependencies from conda-forge (pre-built binaries for lxml/pandas)
conda install -c conda-forge pandas lxml requests beautifulsoup4 python-dateutil -y

# 4. Verify
python -c "import requests, bs4, lxml, pandas, dateutil; print('✓ All good')"
```

### Option B — Pip

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### `requirements.txt`

```txt
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
pandas>=2.0.0
python-dateutil>=2.8.2
```

---

## ⚡ Quick Start

```bash
# 1. Clone / cd into the project
cd scraper

# 2. Activate environment
conda activate scraper

# 3. Run the bundled example (scrapes books.toscrape.com)
python main.py --site books
```

**Expected output:**

```
2026-11-04 12:00:01 | INFO  | __main__ | === Starting scrape: books_toscrape ===
2026-11-04 12:00:02 | INFO  | scraper  | [books_toscrape] Fetching page 1: https://books.toscrape.com/catalogue/page-1.html
2026-11-04 12:00:04 | INFO  | scraper  |   -> extracted 20 records
2026-11-04 12:00:07 | INFO  | scraper  | [books_toscrape] Fetching page 2: ...
2026-11-04 12:00:09 | INFO  | scraper  |   -> extracted 20 records
2026-11-04 12:00:12 | INFO  | scraper  | [books_toscrape] Fetching page 3: ...
2026-11-04 12:00:14 | INFO  | scraper  |   -> extracted 20 records
2026-11-04 12:00:14 | INFO  | scraper  | [books_toscrape] Total raw records: 60
2026-11-04 12:00:14 | INFO  | cleaner  | Raw DataFrame shape: (60, 6)
2026-11-04 12:00:14 | INFO  | cleaner  | Deduped on ['title']: 60 -> 60 rows
2026-11-04 12:00:14 | INFO  | cleaner  | Null counts: {'title': 0, 'price': 0, ...}
2026-11-04 12:00:14 | INFO  | exporter | ✓ Exported 60 rows -> output/books_toscrape.csv
2026-11-04 12:00:14 | INFO  | exporter | ✓ Exported 60 rows -> output/books_toscrape.json
2026-11-04 12:00:14 | INFO  | __main__ | === Done: 60 clean rows saved ===
```

Files appear in `output/`:

```
output/books_toscrape.csv
output/books_toscrape.json
```

---

## ⚙️ Configuration Reference

All configuration lives in `config.py`. Each site is a `SiteConfig` dataclass.

### `SiteConfig` fields

| Field | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | **required** | Unique site identifier (used as output filename). |
| `start_url` | `str` | **required** | First page URL to fetch. |
| `container_selector` | `str` | **required** | CSS selector matching each item/card block. |
| `field_map` | `Dict[str, str]` | **required** | `{field_name: css_selector}` — extracts **text**. |
| `attr_map` | `Dict[str, str]` | `{}` | `{field_name: css_selector}` — extracts `href`/`src` from matched node. |
| `pagination_selector` | `str \| None` | `None` | CSS selector for the "next page" link. `None` disables pagination. |
| `next_page_attr` | `str` | `"href"` | Attribute on the pagination node holding the next URL. |
| `max_pages` | `int` | `5` | Max pages to crawl per run. |
| `rate_limit_seconds` | `float` | `1.5` | Base delay between requests. |
| `jitter_seconds` | `float` | `0.5` | Random delay added on top (0 to this value). |
| `timeout_seconds` | `int` | `15` | Per-request HTTP timeout. |
| `max_retries` | `int` | `3` | Retry attempts per URL. |
| `dtypes` | `Dict[str, str]` | `{}` | `{field_name: "int"\|"float"\|"datetime"\|"str"}` |
| `strip_patterns` | `Dict[str, str]` | `{}` | `{field_name: regex}` — regex removed before casting. |
| `primary_keys` | `List[str]` | `[]` | Column(s) used for deduplication. |

### Example configuration

```python
BOOKS_CONFIG = SiteConfig(
    name="books_toscrape",
    start_url="https://books.toscrape.com/catalogue/page-1.html",
    container_selector="article.product_pod",
    field_map={
        "title": "h3 a",
        "price": "p.price_color",
        "availability": "p.instock.availability",
        "rating": "p.star-rating",
    },
    attr_map={
        "product_url": "h3 a",
        "image_url": "img",
    },
    pagination_selector="li.next a",
    max_pages=3,
    rate_limit_seconds=1.0,
    jitter_seconds=0.3,
    dtypes={"price": "float"},
    strip_patterns={"price": r"[^\d.]"},
    primary_keys=["title"],
)
```

**What this does:**

- Scrapes up to 3 pages of books.
- Extracts 6 fields per book (4 as text, 2 as attributes).
- Converts `price` from `"£51.77"` → `51.77` (float).
- Removes duplicate books by title.
- Waits ~1–1.3s between requests.

---

## ➕ Adding a New Target Site

**No code changes required outside `config.py`.** Three steps:

### Step 1 — Inspect the site

Open DevTools (F12) on the target page and note:

- The **item container** CSS selector (e.g., `.product`, `article.item`).
- Each **field's** CSS selector **relative to the container**.
- The **next page** selector (if paginated).

### Step 2 — Add a `SiteConfig`

```python
MY_SITE_CONFIG = SiteConfig(
    name="my_site",
    start_url="https://example.com/products?page=1",
    container_selector="div.product-card",
    field_map={
        "name": "h2.product-title",
        "description": "p.desc",
        "price": "span.price",
    },
    attr_map={
        "detail_url": "a.product-link",
        "thumbnail": "img.thumb",
    },
    pagination_selector="a.next-page",
    max_pages=5,
    dtypes={"price": "float"},
    strip_patterns={"price": r"[^\d.]"},
    primary_keys=["detail_url"],
)
```

### Step 3 — Register in `SITES`

```python
SITES = {
    "books": BOOKS_CONFIG,
    "quotes": QUOTES_CONFIG,
    "mysite": MY_SITE_CONFIG,   # ← add this line
}
```

### Step 4 — Run

```bash
python main.py --site mysite
```

---

## 💻 CLI Reference

```bash
python main.py --help
```

```
usage: main.py [-h] --site {books,mysite,quotes} [--output-dir OUTPUT_DIR]
               [--log-level {DEBUG,INFO,WARNING,ERROR}]

Config-driven web scraper + cleaner.

options:
  -h, --help            show this help message and exit
  --site {books,mysite,quotes}
                        Registered site config name.
  --output-dir OUTPUT_DIR
                        Output directory (default: output).
  --log-level {DEBUG,INFO,WARNING,ERROR}
                        Logging verbosity (default: INFO).
```

### Examples

```bash
# Default run
python main.py --site books

# Custom output directory
python main.py --site books --output-dir data/november

# Verbose debugging
python main.py --site books --log-level DEBUG

# Quiet run (only warnings/errors)
python main.py --site quotes --log-level WARNING
```

**Exit codes:**

| Code | Meaning |
|---|---|
| `0` | Success — data cleaned and exported |
| `1` | Failure — no records extracted (all pages failed or selectors wrong) |

---

## 📤 Output Format

### CSV — `output/<site_name>.csv`

- UTF-8 with BOM (`utf-8-sig`) — opens cleanly in Excel.
- Header row + one row per record.
- Nested fields are **not** supported (flat schema only).

### JSON — `output/<site_name>.json`

- Array of objects, pretty-printed (`indent=2`).
- Datetimes converted to ISO strings.
- `ensure_ascii=False` — preserves Unicode.

**Sample `books_toscrape.json`:**

```json
[
  {
    "title": "A Light in the Attic",
    "price": 51.77,
    "availability": "In stock",
    "rating": "Three",
    "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    "image_url": "https://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg"
  },
  {
    "title": "Tipping the Velvet",
    "price": 53.74,
    "availability": "In stock",
    "rating": "One",
    "product_url": "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html",
    "image_url": "https://books.toscrape.com/media/cache/26/0c/260c6ae16bce31c8f8c95dadd5e3a7e9.jpg"
  }
]
```

---

## 🏗️ How It Works (Architecture)

```
┌──────────────────────────────────────────────────────────────────┐
│                         main.py (CLI)                            │
│  parse args → load SiteConfig → scrape → clean → export          │
└──────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│      scraper.py         │
│  ┌───────────────────┐  │      ┌─────────────────────────────┐
│  │   HttpClient      │  │─────▶│  Target website (HTTP)      │
│  │ - Session         │  │      └─────────────────────────────┘
│  │ - Rate limiting   │  │
│  │ - Retries/backoff │  │
│  │ - UA header       │  │
│  └───────────────────┘  │
│           │              │
│           ▼              │
│  extract_items_from_page │───────▶ List[Dict] (raw records)
│  find_next_page          │
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│      cleaner.py         │
│  clean_dataframe()      │───────▶ pd.DataFrame (typed, deduped)
│  - dtype casting        │
│  - strip patterns       │
│  - dedupe on keys       │
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│      exporter.py        │
│  export_dataframe()     │───────▶ output/<name>.csv
│  - mkdir -p output      │───────▶ output/<name>.json
│  - CSV + JSON writes    │
│  - Summary stats log    │
└─────────────────────────┘
```

### Design principles

1. **Separation of concerns** — each module is independently testable.
2. **Schema-as-data** — the `SiteConfig` is the only site-specific artifact.
3. **Fail-safe** — missing elements → `None`; failed pages → logged and skipped; failed requests → retried with backoff.
4. **Polite by default** — 1.5s + jitter between requests.
5. **Idempotent** — re-running overwrites output with fresh, deduped data.

---

## 🔌 Extending the Framework

### Add a new dtype (e.g., `bool`)

In `cleaner.py`:

```python
def _cast_value(value, dtype, strip_pattern=None):
    ...
    if dtype == "bool":
        return str(s).lower() in ("1", "true", "yes")
    ...
```

Then use `dtypes={"in_stock": "bool"}` in config.

### Add a new attribute extractor

`scraper.py` currently guesses `href`/`src` by tag name. For custom attributes:

```python
attr_map = {
    "data_id": ("div.item", "data-id"),   # (selector, attribute)
}
```

You'd extend `attr_map` to support tuple values, then update `extract_items_from_page` accordingly.

### Custom cleaning hook

In `cleaner.py`, add per-column transforms:

```python
def clean_dataframe(raw_records, config, custom_hook=None):
    ...
    if custom_hook:
        df = custom_hook(df)
    ...
```

Then in `main.py`:

```python
df = clean_dataframe(
    raw_records, config,
    custom_hook=lambda d: d.assign(title=d["title"].str.upper()),
)
```

### Add a per-page callback (e.g., incremental save)

In `scraper.py`, `scrape_site` already processes pages in a loop. Add:

```python
def scrape_site(config, on_page=None):
    ...
    if on_page:
        on_page(page_num, records)
    ...
```

---

## 🩺 Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `0 records extracted` | Wrong `container_selector` | Inspect DOM; test `soup.select(container_selector)` in a Python REPL |
| Some fields are `None` | Wrong field selector or the site uses JS rendering | Check with `--log-level DEBUG`; for JS-rendered sites, see [Selenium note](#faq) |
| `price` is `None` | Strip regex too greedy | Test regex with `re.sub(r"[^\d.]", "", "£51.77")` → `"51.77"` |
| `HTTP 403` | Site blocks default Python UA or you | Ensure custom UA is set (already default); slow down `rate_limit_seconds` |
| `HTTP 429` | Rate limit exceeded | Increase `rate_limit_seconds` to `3.0+` |
| `Max retries exceeded` | Network or site down | Check `curl <url>` manually |
| `lxml install fails on pip` | No pre-built wheel | Use conda: `conda install -c conda-forge lxml` |
| `UnicodeDecodeError` in output | Bad encoding on target | Rare; `requests` uses `resp.text` — consider `resp.content.decode("utf-8", errors="ignore")` |
| Partial data across runs | Site changed | Re-inspect selectors; `max_pages` may have been hit |
| `ModuleNotFoundError: config` | Running outside project dir | `cd` to repo root |

### Debugging a specific page

```python
# debug.py — quick harness
from config import SITES
from scraper import HttpClient, extract_items_from_page

cfg = SITES["books"]
client = HttpClient(cfg)
resp = client.get(cfg.start_url)
records = extract_items_from_page(resp.text, cfg, cfg.start_url)
print(f"Found {len(records)} records")
print(records[:2])
client.close()
```

Run: `python debug.py`

---

## ⚖️ Best Practices & Legal Notes

- **Read `robots.txt`** of every target site. `https://example.com/robots.txt`.
- **Respect rate limits.** Default is polite (≥1s + jitter). Don't lower it without cause.
- **Don't scrape personal data** or content behind authentication without permission.
- **Check Terms of Service.** Some sites forbid automated access.
- **Cache results.** Avoid re-scraping unnecessarily; use `max_pages` intentionally.
- **Identify yourself.** Consider setting a custom UA with contact info for large-scale jobs:

  ```python
  HttpClient(config, user_agent="MyScraper/1.0 (+https://my.site/bot)")
  ```
- **Prefer official APIs** when available — they're faster, more stable, and legal.

---

## ❓ FAQ

### Does this handle JavaScript-rendered sites?

No — it uses `requests` + `BeautifulSoup`, which do **not** execute JS. For SPA / JS-heavy sites (React, Vue, etc.), either:

1. Use the site's underlying JSON API (inspect DevTools → Network tab), or
2. Swap `HttpClient.get` for a Selenium/Playwright fetcher.

### Can I scrape sites that require login?

Yes, but you must handle it explicitly. Simplest approach — inject cookies:

```python
client = HttpClient(config)
client.session.cookies.set("session", "<your-cookie>")
```

Or perform a login POST first (add a `login()` method to `HttpClient`).

### Can I scrape multiple sites in one run?

Yes — loop over them:

```python
for name in ["books", "quotes"]:
    config = SITES[name]
    raw = scrape_site(config)
    df = clean_dataframe(raw, config)
    export_dataframe(df, "output", config.name)
```

### How do I scrape more than 5 pages?

Increase `max_pages` in the `SiteConfig`.

### Can I run this on a schedule?

Yes — wrap in cron (Linux/macOS) or Task Scheduler (Windows):

```cron
# Every day at 2 AM
0 2 * * * cd /path/to/scraper && /opt/conda/envs/scraper/bin/python main.py --site books
```

Or use GitHub Actions — commit the outputs to a branch.

### How do I add unit tests?

```python
# test_scraper.py
from bs4 import BeautifulSoup
from scraper import extract_items_from_page, _safe_text
from config import BOOKS_CONFIG

def test_safe_text_missing():
    assert _safe_text(None) is None

def test_extract_from_html():
    html = """
    <article class="product_pod">
      <h3><a href="/x">Title A</a></h3>
      <p class="price_color">£10.00</p>
    </article>
    """
    records = extract_items_from_page(html, BOOKS_CONFIG, "https://x.com")
    assert records[0]["title"] == "Title A"
    assert records[0]["product_url"] == "https://x.com/x"
```

Run: `pytest test_scraper.py -v`

### Where's the roadmap?

- [ ] Optional Selenium backend for JS-rendered sites
- [ ] Concurrent fetching (async or thread pool)
- [ ] Schema validation via `pandera` or `pydantic`
- [ ] SQLite / Postgres sinks
- [ ] Resumable crawl (checkpoint pagination state)
- [ ] HTML snapshot cache for offline debugging

---

## 📄 License

Add your license here. For most scraping tools, **MIT** is a common choice. If you plan to publish, include a `LICENSE` file.

---

## 🙌 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-improvement`
3. Commit: `git commit -m "feat: add X"`
4. Push: `git push origin feature/my-improvement`
5. Open a Pull Request

Please run `pytest` before submitting PRs.

---

**Built with `requests`, `beautifulsoup4`, `lxml`, `pandas`, and a lot of care for clean architecture.** 🧹
