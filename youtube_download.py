# from faster_whisper import WhisperModel

# model = WhisperModel("large-v2", device="cpu", compute_type="float16")
# path = "downloads/dQw4w9WgXcQ.mp4"

# segments, info = model.transcribe(path, language="en")
# text = " ".join([segment.text for segment in segments])
# print(text[:500])  # Print the first 500 characters of the transcript

# text = " ".join([c.text.strip().replace("\n", "") for c in webvtt.read(path)])
# print(text[:500])  # Print the first 500 characters of the transcript
from faster_whisper import WhisperModel

path = "downloads/dQw4w9WgXcQ.mp4"

model = WhisperModel("base", device="cpu")
segments, info = model.transcribe(path, language="en")

text = " ".join([seg.text for seg in segments])
print(text[:500])

# from langchain.docstore.document import Document
# from langchain.text_splitter import RecursiveCharacterTextSplitter

# doc = Document(page_content = text, metadata={"source": path})
# splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
# docs = splitter.split_documents([doc])
# chunks = splitter.split_documents([doc])

# print(len(chunks), "chunks created.")
# print(chunks[0].page_content[:300])  # Print the first 500 characters