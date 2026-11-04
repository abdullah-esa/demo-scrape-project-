"""
Site configuration definitions.

To point the framework at a new site, add a new SiteConfig entry.
No code changes are required elsewhere.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class SiteConfig:
    name: str
    start_url: str
    container_selector: str                # CSS selector for each item card
    field_map: Dict[str, str]              # field_name -> CSS selector
    attr_map: Dict[str, str] = field(default_factory=dict)  # field -> attribute (e.g. 'href')
    pagination_selector: Optional[str] = None   # CSS selector for "next page" link
    next_page_attr: str = "href"
    max_pages: int = 5
    rate_limit_seconds: float = 1.5
    jitter_seconds: float = 0.5
    timeout_seconds: int = 15
    max_retries: int = 3
    # Cleaning schema: field -> target dtype
    dtypes: Dict[str, str] = field(default_factory=dict)
    # Strip patterns applied during cleaning
    strip_patterns: Dict[str, str] = field(default_factory=dict)
    # Primary key(s) for dedupe
    primary_keys: list = field(default_factory=list)


# ---- Sample configuration: books.toscrape.com ----
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
        "product_url": "h3 a",       # extract from <a href="...">
        "image_url": "img",          # extract from <img src="...">
    },
    pagination_selector="li.next a",
    next_page_attr="href",
    max_pages=3,
    rate_limit_seconds=1.0,
    jitter_seconds=0.3,
    dtypes={
        "title": "str",
        "price": "float",            # £51.77 -> 51.77
        "availability": "str",
        "rating": "str",
        "product_url": "str",
        "image_url": "str",
    },
    strip_patterns={
        "price": r"[^\d.]",          # keep digits and decimal point
        "rating": r"^star-rating\s*",# remove prefix class text
        "availability": r"\s+",
    },
    primary_keys=["title"],
)


# ---- Example: a second site (demonstrates adaptability) ----
QUOTES_CONFIG = SiteConfig(
    name="quotes_toscrape",
    start_url="https://quotes.toscrape.com/page/1/",
    container_selector="div.quote",
    field_map={
        "quote": "span.text",
        "author": "small.author",
    },
    attr_map={
        "author_url": "small.author a",   # if <a> exists; else safe (None)
    },
    pagination_selector="li.next a",
    max_pages=2,
    dtypes={"quote": "str", "author": "str", "author_url": "str"},
    primary_keys=["quote", "author"],
)


# Registry — pass --site <name> on CLI
SITES = {
    "books": BOOKS_CONFIG,
    "quotes": QUOTES_CONFIG,
}