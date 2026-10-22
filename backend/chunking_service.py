
from langchain_core.documents import Document


def create_transcript_chunks(
    segments: list[dict],
    max_chars: int = 1000,
    overlap_segments: int = 2
) -> list[Document]:

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")

    if overlap_segments < 0:
        raise ValueError("overlap_segments cannot be negative")

    if not segments:
        return []

    # Step 1: Split transcript into groups of captions
    chunks = []
    current_chunk = []
    current_length = 0

    for segment in segments:
        text_length = len(segment["text"])

        separator_length = 1 if current_chunk else 0

        if (
            current_chunk
            and current_length + separator_length + text_length > max_chars
        ):
            chunks.append(current_chunk)
            current_chunk = []
            current_length = 0
            separator_length = 0

        current_chunk.append(segment)
        current_length += separator_length + text_length

    if current_chunk:
        chunks.append(current_chunk)

    # Step 2: Add caption overlap
    documents = []

    for index, chunk in enumerate(chunks):

        if index > 0 and overlap_segments > 0:
            previous_chunk = chunks[index - 1]
            overlap = previous_chunk[-overlap_segments:]
            chunk = overlap + chunk

        # Step 3: Combine caption text
        chunk_text = " ".join(
            segment["text"] for segment in chunk
        )

        # Step 4: Preserve timestamps
        start_time = min(
            segment["start"] for segment in chunk
        )

        end_time = max(
            segment["start"] + segment["duration"]
            for segment in chunk
        )

        # Step 5: Create LangChain Document
        document = Document(
            page_content=chunk_text,
            metadata={
                "video_id": chunk[0]["video_id"],
                "start": start_time,
                "end": end_time,
                "chunk_index": index
            }
        )

        documents.append(document)

    return documents
