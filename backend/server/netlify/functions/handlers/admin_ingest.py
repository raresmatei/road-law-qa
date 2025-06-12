# backend/server/netlify/functions/handlers/admin_ingest.py

import os
import sys
from typing import List
from fastapi import HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer


# ─── Settings / environment ─────────────────────────────────────────────────
from backend.scrape_api.crawler import crawl
from backend.scrape_api.html_parser import chunk_text, parse_html
from backend.server.netlify.utils.settings import settings

PINECONE_KEY   = settings.PINECONE_API_KEY
PINECONE_ENV   = settings.PINECONE_ENV
PINECONE_INDEX = settings.PINECONE_INDEX

# ─── Pydantic request/response schemas ──────────────────────────────────────
class IngestRequest(BaseModel):
    url: HttpUrl

class IngestResponse(BaseModel):
    inserted_chunks: int

# ─── URL → “name” helper ─────────────────────────────────────────────────────
def get_name_from_url(url: str) -> str:
    from urllib.parse import urlparse, unquote, quote_plus
    from uuid import uuid4

    parsed = urlparse(url)
    segment = parsed.path.rstrip("/").split("/")[-1]
    name = unquote(segment) if segment else ""
    if name == "PDF":
        return str(uuid4())
    if not name:
        name = quote_plus(parsed.netloc + parsed.path)
    return name.replace(" ", "_")

# ─── Pinecone + model initialization ────────────────────────────────────────
pc = Pinecone(api_key=PINECONE_KEY, environment=PINECONE_ENV)
if PINECONE_INDEX not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV),
    )
_index = pc.Index(PINECONE_INDEX)

EMBED_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
_model = SentenceTransformer(EMBED_MODEL)


async def ingest_legislation_admin(
    req: IngestRequest,
    user_id: str = Depends(...),  # use your get_current_admin_user here
) -> IngestResponse:
    # ─── 0) Prevent duplicate ingestion ───────────────────────────────────
    stats = _index.describe_index_stats()
    dim = stats["dimension"]
    # dummy zero-vector to allow use of metadata filter
    dummy_vector = [0.0] * dim
    dup_check = _index.query(
        vector=dummy_vector,
        filter={"url": {"$in": [req.url]}},
        top_k=1,
        include_metadata=False,
    )
    if dup_check.matches:
        raise HTTPException(
            status_code=400,
            detail=f"Legislation at URL {req.url} has already been ingested."
        )

    try:
        # ─── 1) Crawl + chunk ───────────────────────────────────────────────
        data = crawl(req.url, max_depth=1)
        grouped: dict[str, List[dict]] = {}
        for e in data:
            grouped.setdefault(e["url"], []).append(e)

        texts: List[str] = []
        metas: List[dict] = []
        for page_url, entries in grouped.items():
            name = get_name_from_url(page_url)
            for e in entries:
                if e.get("type") == "html":
                    for chunk in parse_html(e):
                        texts.append(chunk["text"])
                        metas.append({
                            "url":         chunk["url"],
                            "name":        name,
                            "chunk_index": chunk["chunk_index"],
                            "text":        chunk["text"],
                        })
                elif e.get("type") == "pdf":
                    for idx, txt in enumerate(chunk_text(e.get("text", ""))):
                        texts.append(txt)
                        metas.append({
                            "url":         page_url,
                            "name":        name,
                            "chunk_index": idx,
                            "text":        txt,
                        })
                else:
                    txt = e.get("text", "")
                    texts.append(txt)
                    metas.append({
                        "url":         page_url,
                        "name":        name,
                        "chunk_index": None,
                        "text":        txt,
                    })

        # ─── 2) Embed ────────────────────────────────────────────────────────
        embeddings = _model.encode(texts, show_progress_bar=False)

        # ─── 3) Upsert in batches ────────────────────────────────────────────
        batch_size = 100
        total = 0
        for i in range(0, len(embeddings), batch_size):
            batch_emb  = embeddings[i : i + batch_size]
            batch_meta = metas[i : i + batch_size]
            vectors = [
                (
                    f"{page_url}#{i+j}",
                    emb.tolist() if hasattr(emb, "tolist") else emb,
                    batch_meta[j],
                )
                for j, emb in enumerate(batch_emb)
            ]
            _index.upsert(vectors=vectors)
            total += len(vectors)

        return IngestResponse(inserted_chunks=total)

    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))
