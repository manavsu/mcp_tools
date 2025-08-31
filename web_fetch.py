# filepath: webfetch_tool.py
from __future__ import annotations

import io
import re
import sys
from typing import Literal, Optional, Dict, Any
from main import mcp
import requests

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:
    BeautifulSoup = None  # type: ignore

try:
    from markdownify import markdownify as md  # type: ignore
except Exception:
    md = None  # type: ignore


MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5MB
DEFAULT_TIMEOUT = 30  # seconds
MAX_TIMEOUT = 120  # seconds

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


# @mcp.tool
def webfetch(
    url: str,
    format: Literal["text", "markdown", "html"],
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Fetch a URL and return content formatted as text, markdown, or html.

    Returns:
      {
        "title": f"{url} ({content-type})",
        "metadata": {},
        "output": "<string>"
      }

    Raises:
      ValueError on invalid input or request/size failures.
    """
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("URL must start with http:// or https://")

    t = timeout if timeout is not None else DEFAULT_TIMEOUT
    if t > MAX_TIMEOUT:
        t = MAX_TIMEOUT

    s = requests.Session()
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Upgrade http -> https with fallback if needed
    u = url
    if u.startswith("http://"):
        https_u = "https://" + u[len("http://") :]
        r = _request(s, https_u, headers, t)
        if not _ok(r):
            r = _request(s, u, headers, t)
    else:
        r = _request(s, u, headers, t)

    if not _ok(r):
        raise ValueError(f"Request failed with status code: {r.status_code}")

    cl = r.headers.get("content-length")
    if cl and cl.isdigit() and int(cl) > MAX_RESPONSE_SIZE:
        raise ValueError("Response too large (exceeds 5MB limit)")

    buf = io.BytesIO()
    for chunk in r.iter_content(chunk_size=65536):
        if not chunk:
            continue
        buf.write(chunk)
        if buf.tell() > MAX_RESPONSE_SIZE:
            raise ValueError("Response too large (exceeds 5MB limit)")

    enc = r.encoding or getattr(r, "apparent_encoding", None) or "utf-8"
    text = buf.getvalue().decode(enc, errors="replace")

    ctype = r.headers.get("content-type", "")
    title = f"{r.url} ({ctype})"

    if format == "text":
        if "text/html" in ctype:
            return {
                "title": title,
                "metadata": {},
                "output": _html_to_text(text),
            }
        return {"title": title, "metadata": {}, "output": text}

    if format == "markdown":
        if "text/html" in ctype:
            return {
                "title": title,
                "metadata": {},
                "output": _html_to_markdown(text),
            }
        return {"title": title, "metadata": {}, "output": f"```\n{text}\n```"}

    # format == "html"
    return {"title": title, "metadata": {}, "output": text}


def _request(
    s: requests.Session, url: str, headers: Dict[str, str], timeout: int
) -> requests.Response:
    return s.get(
        url, headers=headers, timeout=timeout, stream=True, allow_redirects=True
    )


def _ok(r: requests.Response) -> bool:
    try:
        return 200 <= r.status_code < 300
    except Exception:
        return False


def _html_to_text(html: str) -> str:
    # Minimal dependency path without BeautifulSoup
    if BeautifulSoup is None:
        # Brutal fallback: strip tags and compress whitespace
        no_script = re.sub(
            r"(?is)<(script|style|noscript|iframe|object|embed).*?>.*?</\1>", " ", html
        )
        stripped = re.sub(r"<[^>]+>", " ", no_script)
        return _normalize_ws(stripped)

    soup = BeautifulSoup(html, "html.parser")
    for tag in ["script", "style", "noscript", "iframe", "object", "embed"]:
        for t in soup.find_all(tag):
            t.decompose()
    # Extract text with spaces, normalize whitespace
    return _normalize_ws(soup.get_text(" "))


def _html_to_markdown(html: str) -> str:
    if md is not None:
        # Reasonable defaults similar to TS turndown config
        return md(
            html,
            heading_style="ATX",
            bullets="*",
            strip=["script", "style", "meta", "link"],
            code_language_callback=lambda _: "",
        ).strip()
    # Fallback: deliver plaintext fenced
    return f"```\n{_html_to_text(html)}\n```"


def _normalize_ws(s: str) -> str:
    s = re.sub(r"\s+", " ", s)
    return s.strip()


print(
    webfetch(
        "https://www.startpage.com/sp/search?query=coding+benchmarks&cat=web&pl=opensearch",
        "text",
    )
)
