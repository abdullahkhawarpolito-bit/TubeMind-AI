
from pathlib import Path
import logging

import chromadb


logger = logging.getLogger(__name__)


# --------------------------------------------------
# ChromaDB configuration
# --------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent

DB_PATH = BACKEND_DIR / "chroma_db"

chroma_client = chromadb.PersistentClient(
    path=str(DB_PATH)
)

collection = chroma_client.get_or_create_collection(
    name="youtube_backend_chunks_v1",
    metadata={"hnsw:space": "cosine"}
)


# --------------------------------------------------
# Store transcript chunks
# --------------------------------------------------

def store_documents(
    documents,
    embeddings
) -> int:
    """
    Store transcript chunks and embeddings
    in the persistent ChromaDB collection.

    Deterministic IDs prevent duplicate records
    when the same chunks are indexed again.
    """

    if not documents:
        return 0

    if len(documents) != len(embeddings):
        raise ValueError(
            "Documents and embeddings must have equal lengths."
        )

    ids = []
    texts = []
    metadatas = []

    for document in documents:
        metadata = document.metadata

        video_id = metadata.get("video_id")
        chunk_index = metadata.get("chunk_index")

        if not video_id:
            raise ValueError(
                "Document metadata is missing video_id."
            )

        if chunk_index is None:
            raise ValueError(
                "Document metadata is missing chunk_index."
            )

        if not document.page_content.strip():
            raise ValueError(
                "Cannot store an empty transcript chunk."
            )

        chunk_id = (
            f"{video_id}_char_v1_{chunk_index}"
        )

        ids.append(chunk_id)
        texts.append(document.page_content)
        metadatas.append(metadata)

    # Validate uniqueness of chunk IDs.
    if len(ids) != len(set(ids)):
        raise ValueError(
            "Duplicate chunk IDs detected in indexing batch."
        )

    # Validate embedding dimensions.
    expected_dimension = None

    for embedding in embeddings:
        if len(embedding) == 0:
            raise ValueError(
                "An embedding vector cannot be empty."
            )

        if expected_dimension is None:
            expected_dimension = len(embedding)

        elif len(embedding) != expected_dimension:
            raise ValueError(
                "Embedding dimensions are inconsistent."
            )

    # Insert or update transcript chunks.
    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    logger.info(
        "Stored %d transcript chunks in ChromaDB",
        len(ids)
    )

    return len(ids)


# --------------------------------------------------
# Search relevant transcript chunks
# --------------------------------------------------

def search_similar_chunks(
    video_id: str,
    query_embedding: list[float],
    top_k: int = 3
) -> list[dict]:
    """
    Retrieve the most similar transcript chunks
    belonging to a specific YouTube video.

    ChromaDB uses cosine distance:
        Smaller distance = greater similarity.

    Approximate cosine similarity:
        similarity = 1 - distance

    Returns each chunk with:
        - text
        - metadata
        - distance
        - similarity
    """

    # Step 1: Validate video ID.
    if not video_id:
        raise ValueError(
            "Video ID cannot be empty."
        )

    # Step 2: Validate query embedding.
    if not query_embedding:
        raise ValueError(
            "Query embedding cannot be empty."
        )

    # Step 3: Validate top_k.
    if top_k <= 0:
        raise ValueError(
            "top_k must be positive."
        )

    # Step 4: Check stored chunks for this video.
    existing = collection.get(
        where={"video_id": video_id},
        include=[]
    )

    available_chunks = len(existing["ids"])

    if available_chunks == 0:
        logger.info(
            "No indexed chunks found for video %s",
            video_id
        )
        return []

    # Step 5: Limit results to available chunks.
    result_count = min(
        top_k,
        available_chunks
    )

    # Step 6: Query ChromaDB.
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=result_count,
        where={"video_id": video_id},
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    documents = results.get("documents") or []
    metadatas = results.get("metadatas") or []
    distances = results.get("distances") or []

    if not documents or not documents[0]:
        logger.info(
            "ChromaDB returned no matching chunks"
        )
        return []

    # Step 7: Prepare chunks and calculate similarity.
    retrieved_chunks = []

    for text, metadata, distance in zip(
        documents[0],
        metadatas[0],
        distances[0]
    ):
        distance = float(distance)

        similarity = 1.0 - distance

        chunk = {
            "text": text,
            "metadata": metadata,
            "distance": distance,
            "similarity": similarity
        }

        retrieved_chunks.append(chunk)

        # Log retrieval information for evaluation.
        logger.info(
            "Retrieved chunk | video=%s | "
            "start=%s | distance=%.4f | similarity=%.4f",
            video_id,
            metadata.get("start"),
            distance,
            similarity
        )

    # Step 8: Log retrieval summary.
    logger.info(
        "Retrieved %d chunks for video %s",
        len(retrieved_chunks),
        video_id
    )

    return retrieved_chunks
