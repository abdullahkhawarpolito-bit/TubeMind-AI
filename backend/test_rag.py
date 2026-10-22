
from indexing_service import index_youtube_video
from embedding_service import generate_query_embedding
from vector_store_service import search_similar_chunks
from generation_service import generate_answer


# Step 1: Enter a YouTube URL and question
url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

question = "What is special about the elephants?"


# Step 2: Index the video if needed
index_result = index_youtube_video(url)

video_id = index_result["video_id"]

print("Indexing status:", index_result["status"])
print("Available chunks:", index_result["chunks"])


# Step 3: Convert the question into an embedding
query_embedding = generate_query_embedding(question)


# Step 4: Retrieve relevant chunks for this video
retrieved_chunks = search_similar_chunks(
    video_id=video_id,
    query_embedding=query_embedding,
    top_k=3
)


# Step 5: Generate an answer using retrieved context
answer = generate_answer(
    question=question,
    retrieved_chunks=retrieved_chunks
)


# Step 6: Display the answer
print("\nQuestion:", question)
print("\nAnswer:")
print(answer)


# Step 7: Display the source timestamp
if retrieved_chunks:

    start_seconds = int(
        retrieved_chunks[0]["metadata"]["start"]
    )

    source_url = (
        f"https://www.youtube.com/watch?v={video_id}"
        f"&t={start_seconds}s"
    )

    print("\nSource:", source_url)
