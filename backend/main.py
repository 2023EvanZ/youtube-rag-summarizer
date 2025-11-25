#     video_id = "UUhy9xSd6zg"
# youtube_ur = "https://www.youtube.com/watch?v=UUhy9xSd6zg"
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import os
import time
import re

from gen_transcript import generate_transcript
from notes_db import save_notes, get_context_from_chromadb, clear_notes_collection

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

class TranscriptRequest(BaseModel):
    youtube_url: str

class RAGRequest(BaseModel):
    question: str

class ChunkRequest(BaseModel):
    file_path: str
    lines_per_chunk: int

load_dotenv()

model = init_chat_model(
    "google_genai:gemini-2.5-flash-lite",
    max_tokens=1000,
    timeout=30
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def chunk_by_lines(file_path, lines_per_chunk=30):
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    chunks = [
        ' '.join(lines[i:i+lines_per_chunk])
        for i in range(0, len(lines), lines_per_chunk)
    ]
    return chunks

def format_note(note):
    #print("ORIGINAL NOTE:", note)
    #print("-" * 40)
    first_star_idx = note.find('*')
    #print("FIRST STAR INDEX:", first_star_idx)
    if first_star_idx == -1:
        return []
    #print("PAST FIRST STAR")
    #print(note[first_star_idx:])
    cleaned = note[first_star_idx:]
    #print("CLEANED:", cleaned)
    bullets = re.split(r'(?<!\*)\*(?!\*)', cleaned)
    formatted_bullets = []
    for bullet in bullets:
        bullet = bullet.strip()
        #print("BULLET:", bullet)
        if bullet:
            bullet = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', bullet)
            formatted_bullets.append(bullet)

    return formatted_bullets

def extract_video_id(youtube_url: str) -> str:
    # Handles various YouTube URL formats
    match = re.search(
        r"(?:v=|\/embed\/|\/shorts\/|youtu\.be\/|\/v\/|\/watch\?v=|\/watch\?.+&v=)([A-Za-z0-9_-]{11})",
        youtube_url
    )
    #print("MATCH:", match)
    if match:
        return match.group(1)
    # Fallback for URLs like https://www.youtube.com/watch?v=VIDEOID
    match = re.search(r"([A-Za-z0-9_-]{11})", youtube_url)
    if match:
        return match.group(1)
    raise ValueError("Could not extract video ID from URL.")

        
@app.post("/transcript")
def process_transcript(req: TranscriptRequest):
    # generate_transcript(req.video_id)
    # return {"status": "transcript generated"}
    print("API FOR GENERATING TRANSCRIPT CALLED WITH URL:", req.youtube_url)
    try:
        video_id = extract_video_id(req.youtube_url)
    except Exception as e:
        return {"error": str(e)}
    generate_transcript(video_id)
    return {"status": "transcript generated"}

@app.post("/chunk")
def chunk_transcript(req: ChunkRequest):
    clear_notes_collection()
    chunks = chunk_by_lines(req.file_path, req.lines_per_chunk)
    notes = []
    base_prompt = (
        "Summarize the important notes and points of the following text. "
        "Make sure it is concise and use bullet points. "
        "Also present the notes in a language that a fifth grade student can understand."
    )
    for i, chunk in enumerate(chunks):
        # Retrieve context from ChromaDB for the current chunk
        context = get_context_from_chromadb(chunk, n_results=3)
        prompt = (
            f"Use the following context to help summarize the chunk:\n\n{context}\n\n"
            f"{base_prompt}\n\nChunk:\n{chunk}"
        )
        response = model.invoke(prompt)
        bullets = format_note(response.content)
        notes.append(bullets)
        #save_notes(bullets, i)
        save_notes(response.content, i)
        time.sleep(20)  # Optional: delay to avoid rate limits
    print("BULLET NOTES:")
    for i, bullets in enumerate(notes):
        print(f"Chunk {i+1} bullets:")
        for bullet in bullets:
            print(f" - {bullet}")
    return {"notes": notes}
# Add more endpoints as needed

# def chunk_by_lines(file_path, lines_per_chunk=10):
#     with open(file_path, 'r') as f:
#         lines = [line.strip() for line in f if line.strip()]
#     chunks = [
#         ' '.join(lines[i:i+lines_per_chunk])
#         for i in range(0, len(lines), lines_per_chunk)
#     ]
#     return chunks

# def answer_with_rag(user_question):
#     context = get_context_from_chromadb(user_question, n_results=3)
#     rag_prompt = ""
#     if context:
#         print("RETRIEVED:")
#         print(context)
#         print("-----------------")
#         rag_prompt = (
#             f"Use the following context to answer the prompt:\n\n{context}\n\n"
#             f"Prompt: {user_question}\n"
#         )
#     return rag_prompt

# def main():
#     prompt = "Summarize the important notes and points of the following text. Make sure it is concise and use bullet points. " \
#     "Also present the notes in a language that a fifth grade student can understand."

#     video_id = "UUhy9xSd6zg"
#     file_path = 'test_transcript.txt'
#     generate_transcript(video_id, file_path)

#     load_dotenv()

#     model = init_chat_model(
#         "google_genai:gemini-2.5-flash-lite",
#         max_tokens=1000,
#         timeout=30
#     )
#     #response = model.invoke("Why do parrots talk?")
#     #print(response.content)

#     #file_path = os.path.join(os.path.dirname(__file__), "test_transcript.txt")
#     try:
#         # with open(file_path, 'r') as file:
#         #     content = file.read()
#         # response = model.invoke(f"{prompt}\n\n{content}")
#         # print(response.content)
#         chunks = chunk_by_lines(file_path, lines_per_chunk=25)
#         for i, chunk in enumerate(chunks):
#             prompt = answer_with_rag(prompt)
#             response = model.invoke(f"{prompt}\n\n{chunk}")
#             print(f"Chunk {i+1} summary:\n{response.content}\n{'-'*40}")
#             save_notes(response.content, i)
#             time.sleep(5)
#     except FileNotFoundError:
#         print(f"Error: The file '{file_path}' was not found.")
#     except Exception as e:
#         print(f"An error occurred: {e}")

# if __name__ == "__main__":
#     main()