# backend/server/netlify/functions/handlers/list_ingested_urls.py

import os
import sys
from typing import List
from fastapi import Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from pinecone import Pinecone, PineconeApiException

from backend.server.netlify.utils.settings import settings
from backend.server.netlify.utils.auth import get_current_admin_user

class UrlsResponse(BaseModel):
    urls: List[HttpUrl]

# initialize Pinecone client & index
pc = Pinecone(api_key=settings.PINECONE_API_KEY, environment=settings.PINECONE_ENV)
if settings.PINECONE_INDEX not in pc.list_indexes().names():
    raise RuntimeError(f"Index {settings.PINECONE_INDEX!r} does not exist")
_index = pc.Index(settings.PINECONE_INDEX)

def list_ingested_urls_handler(
    user_id: str = Depends(get_current_admin_user),
) -> UrlsResponse:
    """
    List all distinct URLs that have already been ingested
    (requires that `url` was indexed in the metadata_config).
    """
    try:
        stats = _index.describe_index_stats()
    except PineconeApiException as e:
        raise HTTPException(status_code=500, detail=str(e))

    ns = stats.get("namespaces", {}).get("", {})
    print('ns: ', ns)
    meta_stats = ns.get("metadata_stats", {}) or ns.get("metadata", {})
    print('meta_stats: ', meta_stats)
    url_counts = meta_stats.get("url", {})

    return UrlsResponse(urls=list(url_counts.keys()))
