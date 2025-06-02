from typing import List, Dict
import re


def chunk_text(text: str, max_words: int = 200, overlap: int = 50) -> List[str]:
    """
    Split text into chunks of up to `max_words` words with an `overlap` of words between chunks.
    """
    words = text.split()
    chunks = []
    start = 0
    total = len(words)
    while start < total:
        end = min(start + max_words, total)
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        start += max_words - overlap
    return chunks


def parse_html(entry: Dict) -> List[Dict]:
    """
    Given an HTML entry, chunk the 'text' with overlap and attach metadata.
    """
    url = entry['url']
    text = entry.get('text', '')
    parsed = []
    for idx, chunk in enumerate(chunk_text(text)):
        parsed.append({'url': url, 'chunk_index': idx, 'text': chunk})
    return parsed
