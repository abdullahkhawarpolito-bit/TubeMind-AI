
from indexing_service import index_youtube_video


url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

result = index_youtube_video(url)

print("Video ID:", result["video_id"])
print("Status:", result["status"])
print("Chunks:", result["chunks"])
