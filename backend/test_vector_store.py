
from transcript_service import (
    extract_video_id,
    get_video_transcript
)

from chunking_service import create_transcript_chunks
from embedding_service import generate_document_embeddings
from vector_store_service import store_documents, collection


url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

video_id = extract_video_id(url)

segments = get_video_transcript(video_id)

documents = create_transcript_chunks(segments)

embeddings = generate_document_embeddings(documents)

stored_count = store_documents(documents, embeddings)

print("Video ID:", video_id)
print("Stored chunks:", stored_count)
print("Collection total:", collection.count())
