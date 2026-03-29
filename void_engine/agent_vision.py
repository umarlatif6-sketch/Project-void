"""
Agent Vision Layer — Web Intelligence APIs

Gives VOID agents real-time external awareness through four specialized APIs:
  - Firecrawl   : Scrapes any URL to clean Markdown (VOID Plane constellation nodes)
  - Tavily      : Multi-step research API (PEACE Token credibility verification)
  - Exa         : Semantic/meaning-based search (Sovereign Realm — acoustic steganography)
  - Brave Search: Independent news feed (Mesa Village agents — unfiltered world context)

All API keys are loaded from environment variables only.
Usage: search(query, mode)  where mode is one of firecrawl|tavily|exa|brave
"""

import os
import logging
import time
import urllib.request
import urllib.error
import urllib.parse
import json
from typing import Optional

logger = logging.getLogger(__name__)

MODES = ["firecrawl", "tavily", "exa", "brave"]

_request_counts = {m: 0 for m in MODES}
_last_errors = {m: None for m in MODES}
_last_request_time = {m: None for m in MODES}


def _env_key(mode: str) -> Optional[str]:
    mapping = {
        "firecrawl": "FIRECRAWL_API_KEY",
        "tavily":    "TAVILY_API_KEY",
        "exa":       "EXA_API_KEY",
        "brave":     "BRAVE_SEARCH_API_KEY",
    }
    key_name = mapping.get(mode)
    if not key_name:
        return None
    return os.environ.get(key_name) or None


def api_status() -> dict:
    """Return live status for all four APIs."""
    statuses = {}
    for mode in MODES:
        key = _env_key(mode)
        statuses[mode] = {
            "configured": key is not None,
            "request_count": _request_counts[mode],
            "last_error": _last_errors[mode],
            "last_request_at": _last_request_time[mode],
        }
    return statuses


def _http_post(url: str, headers: dict, body: dict, timeout: int = 15) -> dict:
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get(url: str, headers: dict, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _search_firecrawl(query: str) -> dict:
    """
    Firecrawl scrape — treats the query as a URL to scrape.
    Falls back to Firecrawl /search endpoint if the query is not a URL.
    """
    key = _env_key("firecrawl")
    if not key:
        raise EnvironmentError("FIRECRAWL_API_KEY is not set")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    if query.startswith("http://") or query.startswith("https://"):
        url = "https://api.firecrawl.dev/v1/scrape"
        body = {"url": query, "formats": ["markdown"]}
        raw = _http_post(url, headers, body)
        markdown = (raw.get("data") or {}).get("markdown", "")
        return {
            "mode": "firecrawl",
            "type": "scrape",
            "url": query,
            "markdown": markdown,
            "char_count": len(markdown),
            "raw": raw,
        }
    else:
        url = "https://api.firecrawl.dev/v1/search"
        body = {"query": query, "limit": 5, "scrapeOptions": {"formats": ["markdown"]}}
        raw = _http_post(url, headers, body)
        results = raw.get("data", [])
        return {
            "mode": "firecrawl",
            "type": "search",
            "query": query,
            "results": results,
            "count": len(results),
            "raw": raw,
        }


def _search_tavily(query: str) -> dict:
    """Tavily multi-step research — environmental credibility verification."""
    key = _env_key("tavily")
    if not key:
        raise EnvironmentError("TAVILY_API_KEY is not set")

    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    body = {
        "api_key": key,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True,
        "max_results": 5,
    }
    raw = _http_post(url, headers, body, timeout=20)
    return {
        "mode": "tavily",
        "query": query,
        "answer": raw.get("answer", ""),
        "results": raw.get("results", []),
        "count": len(raw.get("results", [])),
        "raw": raw,
    }


def _search_exa(query: str) -> dict:
    """Exa semantic search — meaning-based, for acoustic steganography research."""
    key = _env_key("exa")
    if not key:
        raise EnvironmentError("EXA_API_KEY is not set")

    url = "https://api.exa.ai/search"
    headers = {
        "x-api-key": key,
        "Content-Type": "application/json",
        "accept": "application/json",
    }
    body = {
        "query": query,
        "type": "neural",
        "numResults": 5,
        "contents": {"text": {"maxCharacters": 1000}},
    }
    raw = _http_post(url, headers, body)
    results = raw.get("results", [])
    return {
        "mode": "exa",
        "query": query,
        "results": results,
        "count": len(results),
        "raw": raw,
    }


def _search_brave(query: str) -> dict:
    """Brave Search — independent news feed for Mesa Village agents."""
    key = _env_key("brave")
    if not key:
        raise EnvironmentError("BRAVE_SEARCH_API_KEY is not set")

    params = urllib.parse.urlencode({"q": query, "count": 10, "search_lang": "en"})
    url = f"https://api.search.brave.com/res/v1/web/search?{params}"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": key,
    }
    raw = _http_get(url, headers)
    web_results = (raw.get("web") or {}).get("results", [])
    return {
        "mode": "brave",
        "query": query,
        "results": web_results,
        "count": len(web_results),
        "raw": raw,
    }


_DISPATCH = {
    "firecrawl": _search_firecrawl,
    "tavily":    _search_tavily,
    "exa":       _search_exa,
    "brave":     _search_brave,
}


def search(query: str, mode: str) -> dict:
    """
    Unified search interface for all four web intelligence APIs.

    Args:
        query: Search query or URL (for firecrawl scrape mode)
        mode:  One of 'firecrawl', 'tavily', 'exa', 'brave'

    Returns:
        dict with at minimum: mode, query, results/content, error (if any)
    """
    mode = (mode or "").lower().strip()
    if mode not in MODES:
        raise ValueError(f"Unknown mode '{mode}'. Valid modes: {MODES}")

    fn = _DISPATCH[mode]
    _last_request_time[mode] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    try:
        result = fn(query)
        _request_counts[mode] += 1
        _last_errors[mode] = None
        logger.info("Agent Vision [%s] query=%r → %d result(s)", mode, query[:80], result.get("count", 1))
        return result
    except EnvironmentError as e:
        _last_errors[mode] = str(e)
        logger.warning("Agent Vision [%s] config error: %s", mode, e)
        raise
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        msg = f"HTTP {e.code}: {e.reason} — {body}"
        _last_errors[mode] = msg
        logger.error("Agent Vision [%s] HTTP error: %s", mode, msg)
        raise RuntimeError(msg) from e
    except Exception as e:
        _last_errors[mode] = str(e)
        logger.error("Agent Vision [%s] error: %s", mode, e)
        raise
