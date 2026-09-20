"""Page fetching + text extraction. httpx/BS4 by default, Playwright optional."""
from __future__ import annotations

import logging
import re
from functools import lru_cache

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; JAAssureResearchBot/1.0; "
        "+https://ja-assure.example/bot)"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Never scrape these — respect robots/terms and avoid obvious PII endpoints.
BLOCKED_HOST_FRAGMENTS = ("facebook.com", "linkedin.com/in/", "instagram.com")


def _blocked(url: str) -> bool:
    return any(frag in url for frag in BLOCKED_HOST_FRAGMENTS)


@lru_cache(maxsize=128)
def _fetch_static(url: str) -> str:
    response = httpx.get(
        url, headers=_HEADERS, timeout=20.0, follow_redirects=True
    )
    response.raise_for_status()
    return response.text


def _fetch_playwright(url: str) -> str:  # pragma: no cover - optional path
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=_HEADERS["User-Agent"])
        page.goto(url, wait_until="networkidle", timeout=30_000)
        html = page.content()
        browser.close()
        return html


def fetch_html(url: str, use_playwright: bool = False) -> str:
    if _blocked(url):
        raise ValueError(f"Refusing to scrape blocked host: {url}")
    if use_playwright:
        try:
            return _fetch_playwright(url)
        except Exception as exc:
            logger.info("playwright failed for %s (%s), falling back", url, exc)
    return _fetch_static(url)


def fetch_text(url: str, use_playwright: bool = False, max_chars: int = 20000) -> str:
    """Fetch a page and return clean, readable text."""
    html = fetch_html(url, use_playwright=use_playwright)
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)[:max_chars]


def extract_emails(text: str) -> list[str]:
    found = EMAIL_RE.findall(text or "")
    # Filter obvious noise.
    clean = [
        e.lower()
        for e in found
        if not e.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
        and "example.com" not in e.lower()
    ]
    seen: set[str] = set()
    out: list[str] = []
    for e in clean:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def extract_phones(text: str) -> list[str]:
    pattern = re.compile(r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{4}")
    return list({m.group(0).strip() for m in pattern.finditer(text or "")})[:5]