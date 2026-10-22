
import os
import logging

from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

from gemini_retry_service import call_gemini_with_retry


logger = logging.getLogger(__name__)


# --------------------------------------------------
# Environment configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is missing from the .env file"
    )


# --------------------------------------------------
# Shared Gemini client
# --------------------------------------------------

client = genai.Client(api_key=api_key)


# --------------------------------------------------
# Document embeddings
# --------------------------------------------------

def generate_document_embeddings(
    documents,
    batch_size: int = 5
) -> list[list[float]]:
    """
    Generate embeddings for transcript documents
    using Gemini in small batches.
    """

    if not documents:
        return []

    if batch_size <= 0:
        raise ValueError(
            "batch_size must be positive"
        )

    all_embeddings = []

    for start in range(
        0,
        len(documents),
        batch_size
    ):
        batch = documents[
            start:start + batch_size
        ]

        texts = [
            document.page_content
            for document in batch
        ]

        response = call_gemini_with_retry(
            lambda: client.models.embed_content(
                model="gemini-embedding-001",
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"
                )
            )
        )

        batch_embeddings = [
            item.values
            for item in response.embeddings
        ]

        if len(batch_embeddings) != len(batch):
            raise ValueError(
                "Embedding count does not match batch size"
            )

        all_embeddings.extend(
            batch_embeddings
        )

        logger.info(
            "Generated embeddings for %d/%d chunks",
            len(all_embeddings),
            len(documents)
        )

    return all_embeddings


# --------------------------------------------------
# Query embedding
# --------------------------------------------------

def generate_query_embedding(
    question: str
) -> list[float]:
    """
    Generate a Gemini query embedding
    for semantic transcript retrieval.
    """

    question = question.strip()

    if not question:
        raise ValueError(
            "Question cannot be empty"
        )

    response = call_gemini_with_retry(
        lambda: client.models.embed_content(
            model="gemini-embedding-001",
            contents=question,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY"
            )
        )
    )

    if not response.embeddings:
        raise RuntimeError(
            "Gemini returned no query embeddings"
        )

    return response.embeddings[0].values
