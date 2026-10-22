
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound
from urllib.parse import urlparse, parse_qs
import re


# Function 1: Extract video ID from a YouTube URL
def extract_video_id(url: str) -> str:

    parsed_url = urlparse(url.strip())

    hostname = (parsed_url.hostname or "").lower()

    if hostname in (
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com"
    ):

        if parsed_url.path == "/watch":
            video_id = parse_qs(
                parsed_url.query
            ).get("v", [None])[0]

        elif parsed_url.path.startswith(("/shorts/", "/live/")):
            video_id = parsed_url.path.split("/")[2]

        else:
            raise ValueError("Unsupported YouTube URL format")

    elif hostname in ("youtu.be", "www.youtu.be"):
        video_id = parsed_url.path.strip("/")

    else:
        raise ValueError("Please enter a valid YouTube URL")

    # Validate the video ID
    if not video_id or not re.fullmatch(
        r"[A-Za-z0-9_-]{11}", video_id
    ):
        raise ValueError("Invalid YouTube video ID")

    return video_id


# Function 2: Fetch transcript for any supported video
def get_video_transcript(video_id: str) -> list[dict]:

    api = YouTubeTranscriptApi()

    # Get all available transcript tracks
    transcript_list = api.list(video_id)

    # Preferred transcript languages
    preferred_languages = ["en", "hi", "ur"]

    selected_transcript = None

    # Try preferred languages one by one
    for language in preferred_languages:

        try:
            selected_transcript = transcript_list.find_transcript(
                [language]
            )
            break

        except NoTranscriptFound:
            continue

    # If preferred languages are unavailable,
    # select the first available transcript
    if selected_transcript is None:

        selected_transcript = next(
            iter(transcript_list),
            None
        )

        if selected_transcript is None:
            raise ValueError(
                "No transcript is available for this video."
            )

    # Fetch the selected transcript
    fetched_transcript = selected_transcript.fetch()

    # Convert transcript captions into dictionaries
    segments = []

    for segment in fetched_transcript:

        segments.append({
            "text": segment.text,
            "start": segment.start,
            "duration": segment.duration,
            "video_id": video_id
        })

    return segments
