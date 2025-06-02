import json
import os
import click
from urllib.parse import urlparse, unquote, quote_plus
from python_be.crawler import crawl
from python_be.html_parser import parse_html, chunk_text
from uuid import uuid4
from uvicorn import run

def get_name_from_url(url: str) -> str:
    """
    Derive a filesystem-safe human-readable name from a URL by extracting the last path segment
    or falling back to a URL-encoded version if no segment is available.
    """
    parsed = urlparse(url)
    segment = parsed.path.rstrip('/').split('/')[-1]
    name = unquote(segment) if segment else ''
    
    print('name: ', name)
    if name == "PDF":
        return str(uuid4())
    if not name:
        # fallback to URL-encoded host+path
        print('not name...')
        name = quote_plus(parsed.netloc + parsed.path)
    # Replace or remove problematic filesystem chars
    return name.replace(' ', '_')

@click.command()
@click.argument('start_url')
@click.option('--out_dir', default='output', help='Directory to store per-URL JSON files')
def main(start_url, out_dir):
    """Crawl and parse legislation site; write one JSON file per parsed URL."""
    # Ensure output directory exists
    os.makedirs(out_dir, exist_ok=True)

    data = crawl(start_url, max_depth=1)
    # Group entries by URL
    grouped = {}
    for e in data:
        grouped.setdefault(e['url'], []).append(e)

    total_files = 0
    # Process each URL group
    for url, entries in grouped.items():
        name = get_name_from_url(url)
        items = []
        for e in entries:
            if e['type'] == 'html':
                # chunk HTML
                for chunk in parse_html(e):
                    items.append({
                        'url': chunk['url'],
                        'name': name,
                        'chunk_index': chunk['chunk_index'],
                        'text': chunk['text']
                    })
            elif e['type'] == 'pdf':
                # chunk PDF text
                for idx, txt in enumerate(chunk_text(e.get('text', ''))):
                    items.append({
                        'url': e['url'],
                        'name': name,
                        'chunk_index': idx,
                        'text': txt
                    })
            else:
                items.append({
                    'url': e['url'],
                    'name': name,
                    'chunk_index': None,
                    'text': e.get('text', '')
                })
        # Write to individual JSON file
        filename = f"{name}.json"
        path = os.path.join(out_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        total_files += 1
        click.echo(f"Wrote {len(items)} chunks for URL {url} to {path}")

    click.echo(f"Completed writing {total_files} files to {out_dir}")
    
def start_server():
    # exactly the same as: uvicorn src.python_be.server.main:app --reload
    run("src.python_be.server.main:app", reload=True)

if __name__ == '__main__':
    main()