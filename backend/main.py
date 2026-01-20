#     video_id = "UUhy9xSd6zg"
# youtube_url = "https://www.youtube.com/watch?v=UUhy9xSd6zg"
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import os
import time
import re
from typing import List

from .gen_transcript import generate_transcript
from .notes_db import save_notes, get_context_from_chromadb, clear_notes_collection, get_transcript_chunks

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

# def chunk_by_lines(file_path, lines_per_chunk=30):
#     with open(file_path, 'r') as f:
#         lines = [line.strip() for line in f if line.strip()]
#     chunks = [
#         ' '.join(lines[i:i+lines_per_chunk])
#         for i in range(0, len(lines), lines_per_chunk)
#     ]
#     return chunks

def strip_html_tags(text: str) -> str:
    """Remove all HTML tags from text and convert to Markdown"""
    # Convert <strong> and <b> to **bold**
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Convert <em> and <i> to *italic*
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<i>(.*?)</i>', r'*\1*', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Convert <u> to __underline__
    text = re.sub(r'<u>(.*?)</u>', r'__\1__', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove any remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def format_note(raw_note: str) -> List[str]:
    """
    Convert LLM output into clean bullet points.
    Strips HTML tags, removes LLM-generated bullets, splits by sentences.
    Returns clean text that can be formatted with bullets later.
    """
    # First, strip all HTML tags and convert to Markdown
    cleaned_note = strip_html_tags(raw_note)
    
    # Split by newlines first to handle existing structure
    lines = cleaned_note.strip().split("\n")
    bullets = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Remove ALL leading bullet markers more aggressively
        # This handles: -, *, •, ◦, numbers, etc.
        line = re.sub(r'^[\-\*\•\◦\▪\▫]+\s*', '', line)  # Remove -, *, bullets
        line = re.sub(r'^\d+[\.\)\:]?\s*', '', line)     # Remove numbers like "1.", "1)", "1:"
        line = re.sub(r'^[a-zA-Z][\.\)]\s*', '', line)   # Remove letters like "a.", "a)"
        
        # Split by sentence boundaries (., !, ?)
        sentences = re.split(r'(?<=[.!?])\s+', line)
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Remove bullet markers again (in case they appear mid-line)
            sentence = re.sub(r'^[\-\*\•\◦\▪\▫]+\s*', '', sentence)
            
            # Remove multiple spaces
            sentence = re.sub(r'\s+', ' ', sentence)
            
            # Skip empty sentences or very short ones
            if sentence and len(sentence) > 3:
                bullets.append(sentence)
    
    return bullets


# def format_note(note):
#     #print("ORIGINAL NOTE:", note)
#     #print("-" * 40)
#     first_star_idx = note.find('*')
#     #print("FIRST STAR INDEX:", first_star_idx)
#     if first_star_idx == -1:
#         return []
#     #print("PAST FIRST STAR")
#     #print(note[first_star_idx:])
#     cleaned = note[first_star_idx:]
#     #print("CLEANED:", cleaned)
#     bullets = re.split(r'(?<!\*)\*(?!\*)', cleaned)
#     formatted_bullets = []
#     for bullet in bullets:
#         bullet = bullet.strip()
#         #print("BULLET:", bullet)
#         if bullet:
#             bullet = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', bullet)
#             formatted_bullets.append(bullet)

#     return formatted_bullets

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
    chunks = get_transcript_chunks(req.lines_per_chunk)
    notes = []
    base_prompt = (
        "Summarize the important notes and points of the following text. "
        "Make sure it is concise and use bullet points. "
        "Also present the notes in a language that a fifth grade student can understand."
        "Use Markdown formatting: **bold** for emphasis, *italic* for secondary emphasis, "
        "and - for bullet points. Do NOT use HTML tags."
    )
    for i, chunk in enumerate(chunks):
        prompt = f"{base_prompt}\n\nChunk:\n{chunk}"
        response = model.invoke(prompt)
        bullets = format_note(response.content)
        notes.append(bullets)
        save_notes(response.content, i)  # Store summary in notes collection
        time.sleep(10)  # Optional: delay to avoid rate limits
    return {"notes": notes}

# @app.post("/chunk")
# def chunk_transcript(req: ChunkRequest):
#     clear_notes_collection()
#     chunks = chunk_by_lines(req.file_path, req.lines_per_chunk)
#     notes = []
#     base_prompt = (
#         "Summarize the important notes and points of the following text. "
#         "Make sure it is concise and use bullet points. "
#         "Also present the notes in a language that a fifth grade student can understand."
#     )
#     for i, chunk in enumerate(chunks):
#         # Retrieve context from ChromaDB for the current chunk
#         context = get_context_from_chromadb(chunk, n_results=3)
#         prompt = (
#             f"Use the following context to help summarize the chunk:\n\n{context}\n\n"
#             f"{base_prompt}\n\nChunk:\n{chunk}"
#         )
#         response = model.invoke(prompt)
#         bullets = format_note(response.content)
#         notes.append(bullets)
#         #save_notes(bullets, i)
#         save_notes(response.content, i)
#         time.sleep(20)  # Optional: delay to avoid rate limits
#     print("BULLET NOTES:")
#     for i, bullets in enumerate(notes):
#         print(f"Chunk {i+1} bullets:")
#         for bullet in bullets:
#             print(f" - {bullet}")
#     return {"notes": notes}
# # Add more endpoints as needed

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