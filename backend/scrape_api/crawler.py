# src/scraper/crawler.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .pdf_extractor import extract_text as extract_pdf_text

# Keep track of visited URLs to avoid infinite loops
visited = set()


def is_pdf_link(url: str) -> bool:
    """
    Determine if a URL points to a PDF resource.
    Checks by:
      1. URL path ending with .pdf or containing '/pdf' segment
      2. HTTP HEAD request for content-type
    """
    parsed = urlparse(url)
    path = parsed.path.lower()
    # Quick path-based check
    if path.endswith('.pdf') or '/pdf' in path:
        return True
    # Fallback: HEAD request to verify content-type
    try:
        resp = requests.head(url, allow_redirects=True, timeout=5)
        content_type = resp.headers.get('content-type', '').lower()
        if 'application/pdf' in content_type:
            return True
    except Exception:
        pass
    return False


def get_links(page_url: str) -> list[dict]:
    """
    Fetch an HTML page and extract all internal <a> links on the same domain.

    Returns:
        A list of dicts with:
          - 'text': link text
          - 'url': absolute URL
    """
    resp = requests.get(page_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')
    base = urlparse(page_url).netloc
    links = []

    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        full_url = urljoin(page_url, href)
        parsed = urlparse(full_url)

        # Only follow links within the same domain
        if parsed.netloc.endswith(base):
            links.append({
                'text': a.get_text(strip=True),
                'url': full_url
            })
            
    print('links: ', links)

    return links


def extract_html_text(page_url: str) -> str:
    """
    Download an HTML page and return its visible text.
    """
    print('page_url: ', page_url)
    resp = requests.get(page_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')
    return soup.get_text(separator='\n', strip=True)


def crawl(start_url: str, max_depth: int = 1) -> list[dict]:
    """
    Crawl from start_url up to max_depth levels (0 = only start_url, 1 = start_url + direct children).
    Returns a list of entries: {'type','url','text','links'?}
    """
    parsed = []

    def _crawl(url: str, depth: int):
        if url in visited or depth > max_depth:
            return
        visited.add(url)

        # Handle PDF links immediately
        if is_pdf_link(url):
            try:
                resp = requests.get(url)
                resp.raise_for_status()
                text = extract_pdf_text(resp.content)
            except Exception:
                text = ''
            parsed.append({'type': 'pdf', 'url': url, 'text': text})
            return

        # Handle HTML page
        try:
            text = extract_html_text(url)
            children = []
            if depth < max_depth:
                children = get_links(url)
        except Exception:
            return

        parsed.append({'type': 'html', 'url': url, 'text': text, 'links': children})
        # Only recurse one more level
        if depth < max_depth:
            for child in children:
                _crawl(child['url'], depth + 1)

    _crawl(start_url, 0)
    return parsed

    