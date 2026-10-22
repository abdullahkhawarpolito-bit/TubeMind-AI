
from transcript_service import extract_video_id
from embedding_service import generate_query_embedding
from vector_store_service import search_similar_chunks


url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

video_id = extract_video_id(url)

question = "What does the speaker say about elephants?"

query_embedding = generate_query_embedding(question)

results = search_similar_chunks(
    video_id=video_id,
    query_embedding=query_embedding,
    top_k=3
)

print("Question:", question)
print("Retrieved chunks:", len(results))

for index, chunk in enumerate(results):
    print(f"\nResult {index + 1}")
    print("Text:", chunk["text"])
    print("Metadata:", chunk["metadata"])
    print("Cosine distance:", chunk["distance"])
