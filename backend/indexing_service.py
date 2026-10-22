
import logging

from transcript_service import (
    extract_video_id,
    get_video_transcript,
)
from chunking_service import create_transcript_chunks
from embedding_service import generate_document_embeddings
from vector_store_service import (
    collection,
    store_documents,
)


logger = logging.getLogger(__name__)


def index_youtube_video(url: str) -> dict:
    """
    Index a YouTube transcript in ChromaDB.

    If the video already has stored chunks,
    skip transcript extraction and embedding.

    Note: This cache assumes existing stored chunks
    represent a completed indexing operation.
    """

    # Step 1: Validate and extract video ID.
    video_id = extract_video_id(url)

    logger.info(
        "Checking indexing cache for video: %s",
        video_id,
    )

    # Step 2: Check ChromaDB for existing chunks.
    existing = collection.get(
        where={"video_id": video_id},
        include=[],
    )

    existing_count = len(existing["ids"])

    if existing_count > 0:
        logger.info(
            "Video %s already indexed (%d chunks)",
            video_id,
            existing_count,
        )

        return {
            "video_id": video_id,
            "status": "already_indexed",
            "chunks": existing_count,
        }

    # Step 3: Fetch transcript.
    logger.info(
        "Fetching transcript for video: %s",
        video_id,
    )

    segments = get_video_transcript(video_id)

    if not segments:
        raise ValueError(
            "No transcript segments found for this video."
        )

    # Step 4: Create transcript chunks.
    documents = create_transcript_chunks(segments)

    if not documents:
        raise ValueError(
            "The transcript could not be divided "
            "into usable chunks."
        )

    logger.info(
        "Created %d transcript chunks for %s",
        len(documents),
        video_id,
    )

    # Step 5: Generate document embeddings.
    embeddings = generate_document_embeddings(
        documents
    )

    if len(embeddings) != len(documents):
        raise RuntimeError(
            "Embedding count does not match "
            "the number of transcript chunks."
        )

    # Step 6: Store chunks in ChromaDB.
    stored_count = store_documents(
        documents,
        embeddings,
    )

    logger.info(
        "Indexed video %s with %d chunks",
        video_id,
        stored_count,
    )

    # Step 7: Return indexing result.
    return {
        "video_id": video_id,
        "status": "indexed",
        "chunks": stored_count,
    }
