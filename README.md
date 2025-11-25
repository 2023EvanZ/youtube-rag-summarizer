# Smart YouTube Summarizer

This is a RAG note-taking application that takes clear and concise notes from YouTube videos.

## Features
- Extracts and chunks YouTube transcripts
- Summarizes content using the Gemini language model
- Stores and retrieves notes and transcripts from ChromaDB Cloud
- Modern React frontend

## Setup
### Backend
1. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. Add your ChromaDB Cloud API key and other secrets to `backend/.env`.
3. Start the backend server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend
1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start the frontend:
   ```bash
   npm start
   ```

## Usage
- Enter a YouTube video URL in the frontend.
- Generate and summarize the transcript.
- View and manage notes.

## Technologies
- FastAPI (Python)
- React (JavaScript)
- ChromaDB Cloud
- LangChain
- YouTube Transcript API

## License
MIT