import chromadb
import uuid
import os
from dotenv import load_dotenv

load_dotenv()
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT = os.getenv("CHROMA_TENANT")
CHROMA_YOUTUBE = os.getenv("CHROMA_YOUTUBE")

chroma_client = chromadb.CloudClient(
  api_key=CHROMA_API_KEY,
  tenant=CHROMA_TENANT,
  database=CHROMA_YOUTUBE
)

notes_collection = chroma_client.get_or_create_collection(name="note_collection")
transcript_collection = chroma_client.get_or_create_collection(name="transcript_collection")

#file_path = "yt_transcript.txt"

def save_notes(notes: str, chunk: int):

    notes_collection.add(
        ids=[str(uuid.uuid4())],
        documents=[notes],
        metadatas=[{"chunk": chunk}]
    )
    print(notes_collection.get()['documents'])
    
def get_context_from_chromadb(query_text, n_results=3):
    results = notes_collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    # Flatten the list of documents
    context = "\n".join([doc for docs in results['documents'] for doc in docs])
    return context

def save_transcript_line(line: str, line_num: int):
    transcript_collection.add(
        ids=[str(uuid.uuid4())],
        documents=[line],
        metadatas=[{"line_num": line_num}]
    )
    # print("TRANSCRIPT COLLECTION:")
    # print(transcript_collection.get()['documents'])
    # print("-" * 30)

def get_context_from_chromadb(query_text, n_results=3):
    results = notes_collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    context = "\n".join([doc for docs in results['documents'] for doc in docs])
    return context

def clear_notes_collection():
    all_docs = notes_collection.get()
    all_ids = all_docs.get("ids", [])
    if all_ids:
        notes_collection.delete(ids=all_ids)
    remaining = notes_collection.get()
    print("Remaining notes after clear:", remaining)
    print("-" * 30)

def clear_transcript_collection():
    all_docs = transcript_collection.get()
    all_ids = all_docs.get("ids", [])
    if all_ids:
        transcript_collection.delete(ids=all_ids)
    remaining = transcript_collection.get()
    print("Remaining transcripts after clear:", remaining)
    print("-" * 30)