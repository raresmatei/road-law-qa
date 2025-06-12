from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from ...utils.settings import settings
from fastapi import HTTPException
from ..schemas.schemas import QueryRequest, Match, QueryResponse

# Load the identical model you used at ingest time
HF_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
hf_model      = SentenceTransformer(HF_MODEL_NAME)

PINECONE_API_KEY = settings.PINECONE_API_KEY
PINECONE_ENV     = settings.PINECONE_ENV
PINECONE_INDEX   = settings.PINECONE_INDEX

if not PINECONE_API_KEY or not PINECONE_ENV:
    raise RuntimeError("Missing PINECONE_API_KEY or PINECONE_ENV")

# Pinecone client + index handle
pc    = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
index = pc.Index(PINECONE_INDEX)

async def query_handler(req: QueryRequest):
    # 1) Embed
    try:
        vec = hf_model.encode([req.query], show_progress_bar=False)[0].tolist()
    except Exception as e:
        raise HTTPException(500, f"Failed to embed query: {e}")

    # 2) Query Pinecone (v2 SDK expects `vector=…`, not `queries=…`)
    try:
        resp = index.query(
            vector=vec,
            top_k=req.top_k,
            include_metadata=True
        )
    except Exception as e:
        raise HTTPException(500, f"Pinecone query error: {e}")

    # 3) Format response
    matches = [
        Match(score=m.score, metadata=m.metadata)
        for m in resp.matches
    ]
    return QueryResponse(matches=matches, prompt=req.query)
