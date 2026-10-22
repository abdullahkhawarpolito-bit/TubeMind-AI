
from transcript_service import (
    extract_video_id,
    get_video_transcript
)

from chunking_service import create_transcript_chunks


# Our longer Hindi tutorial
url = "https://www.youtube.com/watch?v=J5_-l7WIO_w"

# Extract video ID
video_id = extract_video_id(url)

# Fetch transcript
segments = get_video_transcript(video_id)

# Create LangChain Documents
documents = create_transcript_chunks(
    segments,
    max_chars=1000,
    overlap_segments=2
)

print("Video ID:", video_id)
print("Transcript segments:", len(segments))
print("Generated chunks:", len(documents))

print("\nFirst chunk metadata:")
print(documents[0].metadata)

print("\nLast chunk metadata:")
print(documents[-1].metadata)
