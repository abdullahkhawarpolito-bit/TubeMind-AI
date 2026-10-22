
from transcript_service import extract_video_id, get_video_transcript
from chunking_service import create_transcript_chunks
from embedding_service import generate_document_embeddings


# Hindi tutorial video
url = "https://www.youtube.com/watch?v=J5_-l7WIO_w"

# Extract transcript and create chunks
video_id = extract_video_id(url)
segments = get_video_transcript(video_id)
documents = create_transcript_chunks(segments)

# Use only 6 chunks for this test
sample_documents = documents[:6]

# Generate embeddings in batches of 5
embeddings = generate_document_embeddings(
    sample_documents,
    batch_size=5
)

print("Video ID:", video_id)
print("Total transcript chunks:", len(documents))
print("Chunks selected for testing:", len(sample_documents))
print("Embeddings generated:", len(embeddings))
print("Embedding dimensions:", len(embeddings[0]))
