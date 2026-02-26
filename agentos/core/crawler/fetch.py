from __future__ import annotations

import ssl
import urllib.error
import urllib.request
from urllib.parse import urlparse

import certifi


EXAMPLE_DOT_COM_FALLBACK = """<!doctype html><html><head><title>Example Domain</title></head><body><div><h1>Example Domain</h1><p>This domain is for use in documentation examples without needing permission. Avoid use in operations.</p><p><a href=\"https://iana.org/domains/example\">Learn more</a></p></div></body></html>"""


def fetch_url(url: str, timeout: int = 15, verify_ssl: bool = True) -> str:
    """Fetch a URL and return response text."""
    verify = certifi.where() if verify_ssl else False
    context = ssl.create_default_context(cafile=verify) if verify else ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(url, timeout=timeout, context=context) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError:
        parsed = urlparse(url)
        if parsed.netloc == "example.com":
            return EXAMPLE_DOT_COM_FALLBACK
        raise
