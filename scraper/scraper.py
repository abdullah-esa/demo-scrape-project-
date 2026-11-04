"""
Request/session management + generic extraction engine.
"""

import logging
import random
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import SiteConfig

logger = logging.getLogger(__name__)

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


class HttpClient:
    """Wraps requests.Session with retries, UA, polite rate-limiting."""

    def __init__(self, config: SiteConfig, user_agent: str = DEFAULT_UA):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        })

    def _throttle(self) -> None:
        delay = self.config.rate_limit_seconds + random.uniform(
            0, self.config.jitter_seconds
        )
        time.sleep(delay)

    def get(self, url: str) -> Optional[requests.Response]:
        """GET with retries. Returns Response or None on total failure."""
        for attempt in range(1, self.config.max_retries + 1):
            try:
                self._throttle()
                resp = self.session.get(url, timeout=self.config.timeout_seconds)
                resp.raise_for_status()
                return resp
            except requests.exceptions.HTTPError as e:
                code = e.response.status_code if e.response is not None else "?"
                logger.warning(
                    f"HTTP {code} on {url} (attempt {attempt}/{self.config.max_retries})"
                )
                # Don't retry client errors (except 429)
                if e.response is not None and 400 <= e.response.status_code < 500 \
                        and e.response.status_code != 429:
                    return None
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Request error on {url} (attempt {attempt}): {e}"
                )
            time.sleep(2 ** attempt)  # exponential backoff
        logger.error(f"Giving up on {url} after {self.config.max_retries} attempts")
        return None

    def close(self) -> None:
        self.session.close()


# ---------- Safe extraction helpers ----------

def _safe_text(node) -> Optional[str]:
    if node is None:
        return None
    text = node.get_text(strip=True)
    return text if text else None


def _safe_attr(node, attr: str) -> Optional[str]:
    if node is None or not hasattr(node, "get"):
        return None
    value = node.get(attr)
    if isinstance(value, list):
        value = " ".join(value)
    return value if value else None


# ---------- Generic extraction ----------

def extract_field(soup_container, selector: str, attr: Optional[str] = None) -> Optional[str]:
    """Extract one field: either text or a specific attribute."""
    node = soup_container.select_one(selector)
    if attr:
        return _safe_attr(node, attr)
    return _safe_text(node)


def extract_items_from_page(
    html: str,
    config: SiteConfig,
    page_url: str,
) -> List[Dict]:
    """Parse one HTML page into a list of raw record dicts."""
    soup = BeautifulSoup(html, "lxml")
    containers = soup.select(config.container_selector)

    records: List[Dict] = []
    for card in containers:
        record: Dict = {}
        for field_name, selector in config.field_map.items():
            record[field_name] = extract_field(card, selector)

        # Attribute-based extraction (e.g. hrefs, srcs)
        for field_name, selector in config.attr_map.items():
            node = card.select_one(selector)
            # Guess attribute: <a> -> href, <img> -> src
            if node is not None:
                if node.name == "a":
                    raw = _safe_attr(node, "href")
                elif node.name == "img":
                    raw = _safe_attr(node, "src")
                else:
                    raw = _safe_text(node)
                # Resolve relative URLs
                if raw and field_name.endswith("_url"):
                    raw = urljoin(page_url, raw)
                record[field_name] = raw
            else:
                record[field_name] = None

        records.append(record)

    return records


def find_next_page(html: str, config: SiteConfig, current_url: str) -> Optional[str]:
    """Return absolute URL of next page, or None."""
    if not config.pagination_selector:
        return None
    soup = BeautifulSoup(html, "lxml")
    node = soup.select_one(config.pagination_selector)
    if node is None:
        return None
    next_href = _safe_attr(node, config.next_page_attr)
    if not next_href:
        return None
    return urljoin(current_url, next_href)


def scrape_site(config: SiteConfig) -> List[Dict]:
    """Full crawl: iterate pagination up to max_pages."""
    client = HttpClient(config)
    all_records: List[Dict] = []
    url: Optional[str] = config.start_url
    page_num = 0

    try:
        while url and page_num < config.max_pages:
            page_num += 1
            logger.info(f"[{config.name}] Fetching page {page_num}: {url}")
            resp = client.get(url)
            if resp is None:
                logger.error(f"[{config.name}] Failed to fetch {url}; stopping.")
                break

            html = resp.text
            records = extract_items_from_page(html, config, url)
            logger.info(f"  -> extracted {len(records)} records")
            all_records.extend(records)

            url = find_next_page(html, config, url)
    finally:
        client.close()

    logger.info(f"[{config.name}] Total raw records: {len(all_records)}")
    return all_records