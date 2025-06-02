import os
from pinecone import Pinecone, ServerlessSpec, CloudProvider, AwsRegion
from typing import List, Tuple, Dict, Any

# -----------------------------------------------------------------------------
# 1) Instantiate the new Pinecone client
# -----------------------------------------------------------------------------
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# -----------------------------------------------------------------------------
# 2) Pick up your index name, dimension and region from env
# -----------------------------------------------------------------------------
INDEX_NAME      = os.getenv("PINECONE_INDEX_NAME", "my-index")
INDEX_DIMENSION = int(os.getenv("PINECONE_INDEX_DIMENSION", "1536"))
REGION          = os.getenv("PINECONE_REGION", "US_EAST_1")  # must match AwsRegion enum

# -----------------------------------------------------------------------------
# 3) Create it if missing (optional) & fetch the host
# -----------------------------------------------------------------------------
existing = pc.list_indexes().names()
if INDEX_NAME not in existing:
    pc.create_index(
        name=INDEX_NAME,
        dimension=INDEX_DIMENSION,
        spec=ServerlessSpec(
            cloud=CloudProvider.AWS,
            region=getattr(AwsRegion, REGION)
        )
    )
index_config = pc.describe_index(INDEX_NAME)

# -----------------------------------------------------------------------------
# 4) Instantiate an Index client against that host
# -----------------------------------------------------------------------------
idx = pc.Index(host=index_config.host)

# -----------------------------------------------------------------------------
# 5) Export your upsert & query functions against idx
# -----------------------------------------------------------------------------
def upsert(
    vectors: List[Tuple[str, List[float], Dict[str, Any]]],
    namespace: str = ""
) -> Dict[str, Any]:
    """
    Upsert a batch of (id, embedding, metadata) into Pinecone.
    """
    return idx.upsert(vectors=vectors, namespace=namespace)

def query_top_k(
    embedding: List[float],
    top_k: int = 10,
    namespace: str = ""
) -> Dict[str, Any]:
    """
    Query Pinecone for the top_k most similar vectors.
    """
    return idx.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace
    )
