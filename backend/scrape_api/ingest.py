# src/python_be/ingest.py

import os
import json
import click
from sentence_transformers import SentenceTransformer

# Pinecone v2 client
from pinecone import Pinecone, ServerlessSpec

@click.command()
@click.argument('dir', type=click.Path(exists=True))
@click.option('--model_name', default='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
@click.option('--pinecone_api_key', envvar='PINECONE_API_KEY', required=True, help='Pinecone API key')
@click.option('--pinecone_env',    envvar='PINECONE_ENV',    required=True, help='Pinecone environment/region')
@click.option('--pinecone_index', default='road-legislation-index', help='Pinecone index name')
def main(dir, model_name, pinecone_api_key, pinecone_env, pinecone_index):
    """Embed JSON text chunks under DIR and upsert to Pinecone."""
    # Instantiate Pinecone client
    pc = Pinecone(api_key=pinecone_api_key, environment=pinecone_env)

    # Create index if missing (adjust `dimension` to your model’s output size)
    existing = pc.list_indexes().names()
    if pinecone_index not in existing:
        pc.create_index(
            name=pinecone_index,
            dimension=384,           # e.g. 384 for MiniLM-L12-v2
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',         # or 'gcp', 'azure'
                region=pinecone_env
            )
        )

    # Connect to it
    index = pc.Index(pinecone_index)

    # Load embedding model
    model = SentenceTransformer(model_name)

    texts, metadata = [], []

    # Read all JSON chunk files
    for fname in os.listdir(dir):
        if not fname.endswith('.json'):
            continue

        path = os.path.join(dir, fname)
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                click.echo(f"❌ Failed to parse {fname}: {e}", err=True)
                continue

        # If you wrote one object per file instead of a list, wrap it
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            click.echo(f"⚠️ Unexpected JSON top‐level type in {fname}: {type(data).__name__}", err=True)
            continue

        for item in data:
            if 'text' not in item:
                click.echo(f"⚠️ Skipping entry in {fname} without 'text': {item}", err=True)
                continue
            texts.append(item['text'])
            metadata.append({
                'url':         item.get('url'),
                'name':        item.get('name'),
                'chunk_index': item.get('chunk_index'),
                'text': item.get('text')
            })

        click.echo(f"✅ Loaded {len(data)} items from {fname}")

    # Encode
    embeddings = model.encode(texts, show_progress_bar=True)

    # Upsert in batches
    batch_size = 100
    for i in range(0, len(embeddings), batch_size):
        batch_emb = embeddings[i:i+batch_size]
        batch_meta = metadata[i:i+batch_size]
        vectors = [
            (str(i + j), emb.tolist(), batch_meta[j])
            for j, emb in enumerate(batch_emb)
        ]
        index.upsert(vectors=vectors)
        click.echo(f"Upserted {len(vectors)} vectors to '{pinecone_index}'")

    click.echo("✅ All embeddings upserted to Pinecone.")

if __name__ == '__main__':
    main()
