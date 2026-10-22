
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from google.genai.errors import ClientError, ServerError

from indexing_service import index_youtube_video
from embedding_service import generate_query_embedding
from vector_store_service import search_similar_chunks
from generation_service import generate_answer
from query_rewriting_service import rewrite_query


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="TubeMind AI API",
    description=(
        "A conversational Retrieval-Augmented Generation "
        "assistant for YouTube video transcripts."
    ),
    version="1.2.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# --------------------------------------------------
# Gemini API error handling
# --------------------------------------------------

@app.exception_handler(ClientError)
async def handle_gemini_client_error(
    request: Request,
    exc: ClientError
):
    status_code = getattr(exc, "code", None)

    if status_code == 429:
        logger.warning(
            "Gemini quota or rate limit exceeded"
        )

        return JSONResponse(
            status_code=429,
            content={
                "detail": (
                    "Gemini API quota or rate limit reached. "
                    "Please wait and try again later."
                )
            },
        )

    if status_code in (401, 403):
        logger.error(
            "Gemini authentication or permission error: %s",
            status_code
        )

        return JSONResponse(
            status_code=502,
            content={
                "detail": (
                    "The AI service is not configured "
                    "correctly. Please contact the "
                    "application administrator."
                )
            },
        )

    logger.error(
        "Gemini client error (status=%s)",
        status_code
    )

    return JSONResponse(
        status_code=502,
        content={
            "detail": (
                "The AI provider could not process "
                "the request. Please try again later."
            )
        },
    )


@app.exception_handler(ServerError)
async def handle_gemini_server_error(
    request: Request,
    exc: ServerError
):
    logger.error(
        "Gemini server error: %s",
        getattr(exc, "code", "unknown")
    )

    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "The Gemini AI service is temporarily "
                "unavailable. Please try again later."
            )
        },
    )


# --------------------------------------------------
# Request models
# --------------------------------------------------

class VideoRequest(BaseModel):
    url: str = Field(
        min_length=1,
        max_length=2048
    )


class ChatMessage(BaseModel):
    role: str = Field(
        pattern="^(user|assistant)$"
    )

    content: str = Field(
        min_length=1,
        max_length=10000
    )


class QuestionRequest(BaseModel):
    url: str = Field(
        min_length=1,
        max_length=2048
    )

    question: str = Field(
        min_length=1,
        max_length=2000
    )

    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=10
    )


# --------------------------------------------------
# Home and health endpoints
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "TubeMind AI API is running",
        "version": "1.2.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "TubeMind AI",
        "version": "1.2.0",
    }


# --------------------------------------------------
# Video indexing
# --------------------------------------------------

@app.post("/index-video")
def index_video(request: VideoRequest):
    """
    Index a YouTube transcript unless the video
    is already available in the vector database.
    """

    try:
        logger.info("Video indexing requested")

        result = index_youtube_video(
            request.url.strip()
        )

        logger.info(
            "Video indexing completed: %s",
            result.get("video_id")
        )

        return result

    except ValueError as error:
        logger.warning(
            "Invalid video request: %s",
            error
        )

        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error


# --------------------------------------------------
# Build verified source references
# --------------------------------------------------

def build_sources(
    video_id: str,
    retrieved_chunks: list[dict],
    source_ids: list[int]
) -> list[dict]:
    """
    Convert selected source IDs into timestamp links.

    Source IDs are 1-based positions in the
    retrieved_chunks list.
    """

    sources = []
    seen_timestamps = set()

    for source_id in source_ids:
        if (
            not isinstance(source_id, int)
            or isinstance(source_id, bool)
        ):
            continue

        chunk_index = source_id - 1

        if not 0 <= chunk_index < len(retrieved_chunks):
            logger.warning(
                "Ignoring out-of-range source ID: %s",
                source_id
            )
            continue

        metadata = (
            retrieved_chunks[chunk_index].get("metadata")
            or {}
        )

        if "start" not in metadata:
            logger.warning(
                "Skipping source without start timestamp"
            )
            continue

        start = float(metadata["start"])
        end = float(metadata.get("end", start))

        timestamp = int(start)

        if timestamp in seen_timestamps:
            continue

        seen_timestamps.add(timestamp)

        source_url = (
            "https://www.youtube.com/watch"
            f"?v={video_id}&t={timestamp}s"
        )

        sources.append({
            "start": start,
            "end": end,
            "url": source_url
        })

    return sources


# --------------------------------------------------
# Conversational RAG endpoint
# --------------------------------------------------

@app.post("/ask")
def ask_question(request: QuestionRequest):
    """
    Conversational RAG pipeline:

    1. Validate question
    2. Ensure video is indexed
    3. Prepare conversation history
    4. Rewrite contextual query when needed
    5. Generate query embedding
    6. Retrieve relevant transcript chunks
    7. Generate answer and supporting source IDs
    8. Build selected timestamp references
    9. Return frontend-compatible response
    """

    try:
        # Step 1: Validate question.
        question = request.question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        logger.info("Processing new RAG question")

        # Step 2: Ensure video is indexed.
        index_result = index_youtube_video(
            request.url.strip()
        )

        video_id = index_result["video_id"]

        logger.info(
            "Processing video: %s",
            video_id
        )

        # Step 3: Prepare conversation history.
        history = [
            message.model_dump()
            for message in request.history[-10:]
        ]

        # Step 4: Rewrite contextual query.
        retrieval_question = rewrite_query(
            question=question,
            history=history
        )

        logger.info(
            "Query rewritten: %s",
            retrieval_question != question
        )

        # Step 5: Generate query embedding.
        query_embedding = generate_query_embedding(
            retrieval_question
        )

        # Step 6: Retrieve transcript chunks.
        retrieved_chunks = search_similar_chunks(
            video_id=video_id,
            query_embedding=query_embedding,
            top_k=5
        )

        logger.info(
            "Retrieved %d transcript chunks",
            len(retrieved_chunks)
        )

        # Step 7: Generate answer and citations.
        if not retrieved_chunks:
            result = {
                "answer": (
                    "I could not find relevant transcript "
                    "content to answer your question."
                ),
                "source_ids": []
            }
        else:
            result = generate_answer(
                question=question,
                retrieved_chunks=retrieved_chunks,
                history=history
            )

        answer = result["answer"]
        source_ids = result["source_ids"]

        # Step 8: Build selected timestamps.
        sources = build_sources(
            video_id=video_id,
            retrieved_chunks=retrieved_chunks,
            source_ids=source_ids
        )

        logger.info(
            "RAG completed | video=%s | "
            "retrieved=%d | cited=%d",
            video_id,
            len(retrieved_chunks),
            len(sources)
        )

        # Step 9: Return frontend-compatible data.
        return {
            "video_id": video_id,
            "question": question,
            "answer": answer,
            "sources": sources,
        }

    except ValueError as error:
        logger.warning(
            "Invalid RAG request: %s",
            error
        )

        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error
