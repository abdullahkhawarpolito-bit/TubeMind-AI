# TubeMind AI — Chat with YouTube Videos

TubeMind AI is a full-stack Retrieval-Augmented Generation (RAG) application that allows users to explore YouTube video content through natural-language conversations.

Instead of manually searching through lengthy videos, users can ask questions, generate summaries, explore key concepts, and navigate directly to relevant video timestamps.

## Features

- **YouTube Transcript Processing:** Extracts available transcripts from supported YouTube videos.
- **Semantic Search:** Retrieves relevant transcript passages using Gemini embeddings and ChromaDB.
- **Context-Aware Conversations:** Supports follow-up questions using recent conversation history and contextual query rewriting.
- **Grounded AI Answers:** Generates answers using retrieved transcript context with Gemini.
- **Clickable Video References:** Provides timestamps linked to relevant moments in the original YouTube video.
- **Persistent Vector Storage:** Caches indexed transcripts to avoid unnecessary reprocessing.
- **Conversation History:** Saves chat sessions locally in the browser.
- **Interactive Interface:** React-based chat interface with video previews, suggested questions, and Markdown-formatted responses.
- **Error Handling:** Handles invalid video URLs, transcript failures, API quota limits, and temporary service errors.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Python, FastAPI, Uvicorn |
| LLM | Google Gemini 2.5 Flash |
| Embeddings | Gemini Embedding (`gemini-embedding-001`) |
| Vector Database | ChromaDB |
| RAG Utilities | LangChain |
| Transcript Extraction | youtube-transcript-api |
| API Communication | REST API |

## RAG Architecture

```text
YouTube Video URL
       |
       v
Transcript Extraction
       |
       v
Text Chunking + Timestamp Metadata
       |
       v
Gemini Document Embeddings
       |
       v
ChromaDB Vector Storage
       |
       v
User Question
       |
       v
Contextual Query Rewriting (when needed)
       |
       v
Query Embedding + Semantic Retrieval
       |
       v
Relevant Transcript Chunks
       |
       v
Gemini Answer Generation
       |
       v
Answer + Selected Video References
```

## Getting Started

### Prerequisites

- Python 3.12
- Node.js and npm
- Google Gemini API key
- Git

### 1. Clone the Repository

```bash
https://github.com/abdullahkhawarpolito-bit/TubeMind-AI.git
cd youtube-transcript-rag
```



### 2. Backend Setup

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Never commit real API keys to GitHub.

### 4. Start the Backend

From the `backend` directory:

```bash
python -m uvicorn main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

### 5. Start the Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## How to Use

1. Open TubeMind AI in your browser.
2. Paste a supported YouTube video URL.
3. Click **Analyze video** to process its transcript.
4. Ask a question or select a suggested prompt.
5. Read the AI-generated answer.
6. Click a video reference timestamp to open the corresponding moment on YouTube.
7. Continue asking follow-up questions.

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Backend service information |
| `/health` | GET | Service health check |
| `/index-video` | POST | Extract and index a video transcript |
| `/ask` | POST | Retrieve context and generate an answer |

## Current Limitations

- Videos must have transcripts accessible through the transcript extraction library.
- Transcript availability can vary by video, language, and YouTube access restrictions.
- Gemini API usage is subject to model availability and rate limits.
- Chat history is stored in browser local storage rather than a user-account database.
- The application is configured for local development; public hosting is not included.

## Project Purpose

TubeMind AI was developed as a practical implementation of Retrieval-Augmented Generation, semantic search, vector databases, conversational AI, and full-stack application development.

The project demonstrates how an LLM can be combined with external knowledge retrieval to generate context-aware answers supported by source references.

## Future Improvements

- Support for multiple videos in a single knowledge base
- Improved retrieval evaluation and answer-quality metrics
- User authentication and cloud-based conversation storage
- Deployment with configurable backend and frontend URLs

## License

No license has been selected yet. All rights reserved unless a license is added.
