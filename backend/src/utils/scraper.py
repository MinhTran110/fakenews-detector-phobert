"""
src/utils/scraper.py
Scrape tiêu đề + nội dung từ URL bài báo tiếng Việt.

Thứ tự ưu tiên:
  1. newspaper3k  — tốt nhất, xử lý hầu hết báo VN
  2. BeautifulSoup với selector riêng cho từng báo lớn
  3. Generic fallback: lấy tất cả <p>
"""
import re
import logging
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# CSS selectors đặc thù cho từng tờ báo lớn VN
DOMAIN_SELECTORS = {
    "vnexpress.net": {
        "title":   ["h1.title-detail", "h1"],
        "content": ["article.fck_detail", "div.content-detail"],
    },
    "tuoitre.vn": {
        "title":   ["h1.article-title", "h1"],
        "content": ["div.detail__content", "div#main-detail-body"],
    },
    "thanhnien.vn": {
        "title":   ["h1.detail-title", "h1"],
        "content": ["div.detail-content", "div#abody"],
    },
    "dantri.com.vn": {
        "title":   ["h1.title-page", "h1"],
        "content": ["div.singular-content", "article"],
    },
    "zingnews.vn": {
        "title":   ["h1.article-title", "h1"],
        "content": ["div.the-article-body", "article"],
    },
    "baomoi.com": {
        "title":   ["h1.bm_S", "h1"],
        "content": ["div.bm_C", "article"],
    },
    "nhandan.vn": {
        "title":   ["h1.article__title", "h1"],
        "content": ["div.article__body", "article"],
    },
    "laodong.vn": {
        "title":   ["h1.article-title", "h1"],
        "content": ["div.article-content", "article"],
    },
}

# Generic fallback selectors
GENERIC_CONTENT_SELECTORS = [
    "article",
    "div.article-body",
    "div.article-content",
    "div.content-detail",
    "div.post-content",
    "div.entry-content",
    "div.content",
    "main",
]


def get_domain(url: str) -> str:
    netloc = urlparse(url).netloc
    return netloc.replace("www.", "").replace("m.", "")


def clean_extracted(text: str, max_len: int = 8000) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()[:max_len]


async def scrape_article(url: str, timeout: int = 15,
                         min_content_len: int = 100,
                         max_content_len: int = 8000) -> dict:
    """
    Trả về:
        {
            "title":   str,
            "content": str,
            "excerpt": str,   # 300 ký tự đầu
            "url":     str,
            "source":  str,   # "newspaper3k" | "beautifulsoup" | "generic"
            "warning": str | None,
        }
    Raises:
        ValueError nếu không đọc được nội dung đủ dài.
    """
    # ── Cách 1: newspaper3k ─────────────────────────────
    try:
        from newspaper import Article
        art = Article(url, language="vi", request_timeout=timeout)
        art.download()
        art.parse()

        title   = art.title or ""
        content = clean_extracted(art.text, max_content_len)

        if len(content) >= min_content_len:
            logger.info(f"[newspaper3k] OK: {url[:60]}")
            return _build_result(title, content, url, "newspaper3k")
    except ImportError:
        logger.debug("newspaper3k not installed, falling back")
    except Exception as e:
        logger.debug(f"[newspaper3k] failed: {e}")

    # ── Cách 2: BeautifulSoup với domain-specific selectors ─
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        raise ValueError(f"Không thể tải trang: {e}")

    soup   = BeautifulSoup(html, "html.parser")
    domain = get_domain(url)

    # Xóa các thẻ không cần thiết
    for tag in soup(["script", "style", "nav", "footer",
                     "header", "aside", "form", "iframe",
                     "noscript", "ads", "advertisement"]):
        tag.decompose()

    # Lấy title
    title = _extract_title(soup, domain)

    # Lấy content
    content, source = _extract_content(soup, domain, max_content_len)

    if len(content) < min_content_len:
        raise ValueError(
            "Không đọc được nội dung. "
            "Trang có thể yêu cầu đăng nhập hoặc chặn bot."
        )

    logger.info(f"[{source}] OK: {url[:60]}")
    warning = None
    if len(content) < 300:
        warning = "Chỉ đọc được một phần nội dung bài báo."

    return _build_result(title, content, url, source, warning)


def _extract_title(soup: BeautifulSoup, domain: str) -> str:
    selectors = DOMAIN_SELECTORS.get(domain, {}).get("title", ["h1"])
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True)

    # Meta fallback
    for meta in [
        soup.find("meta", property="og:title"),
        soup.find("meta", attrs={"name": "title"}),
    ]:
        if meta and meta.get("content"):
            return meta["content"].strip()

    if soup.title:
        return soup.title.string or ""
    return ""


def _extract_content(soup: BeautifulSoup, domain: str,
                     max_len: int) -> tuple[str, str]:
    # Domain-specific selectors
    selectors = DOMAIN_SELECTORS.get(domain, {}).get("content", [])
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = _paragraphs_to_text(el)
            if len(text) > 200:
                return clean_extracted(text, max_len), "beautifulsoup"

    # Generic selectors
    for sel in GENERIC_CONTENT_SELECTORS:
        el = soup.select_one(sel)
        if el:
            text = _paragraphs_to_text(el)
            if len(text) > 200:
                return clean_extracted(text, max_len), "generic"

    # Last resort: tất cả <p> trên trang
    paragraphs = soup.find_all("p")
    text = " ".join(
        p.get_text(strip=True)
        for p in paragraphs
        if len(p.get_text(strip=True)) > 30
    )
    return clean_extracted(text, max_len), "fallback"


def _paragraphs_to_text(element: BeautifulSoup) -> str:
    paragraphs = element.find_all(["p", "h2", "h3"])
    if paragraphs:
        return " ".join(p.get_text(strip=True) for p in paragraphs)
    return element.get_text(separator=" ", strip=True)


def _build_result(title: str, content: str, url: str,
                  source: str, warning: str | None = None) -> dict:
    return {
        "title":   title,
        "content": content,
        "excerpt": content[:300] + ("…" if len(content) > 300 else ""),
        "url":     url,
        "source":  source,
        "warning": warning,
    }


def is_valid_article_url(url: str) -> bool:
    """Heuristic kiểm tra URL có phải là bài viết không."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.netloc:
            return False
        path = parsed.path.rstrip("/")
        # URL bài viết thường có path >= 2 cấp hoặc chứa slug
        return (
            path.count("/") >= 2
            or any(x in url for x in [".html", ".htm", "-p", "/bai-viet"])
        )
    except Exception:
        return False
