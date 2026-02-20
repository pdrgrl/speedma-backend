import os
import glob
from pathlib import Path
from dotenv import load_dotenv

# Try importing the required libraries, but catch errors if running in an environment without them
try:
    import chromadb
    from google import genai
    from google.genai import types
except ImportError:
    print("Please install requirements: pip install google-genai chromadb python-dotenv")
    exit(1)

# 1. Setup and Initialization
load_dotenv()  # Loads GEMINI_API_KEY from .env file

if not os.environ.get("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY environment variable not set. Please add it to your .env file.")

print("Initializing Gemini and ChromaDB clients...")
# Initialize Gemini client (it automatically picks up GEMINI_API_KEY)
gemini_client = genai.Client()

# Initialize ChromaDB persistent client (saves to local disk)
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Use get_or_create to avoid errors if running multiple times
collection = chroma_client.get_or_create_collection(name="chamusca_corpus")

# 2. Read and Chunk Markdown Documents
def chunk_markdown(text):
    """
    Splits markdown text into chunks based on H2 (##) headers.
    This preserves the natural structural boundaries of the document.
    """
    sections = text.split("\n## ")
    chunks = []
    for i, sec in enumerate(sections):
        if not sec.strip():
            continue
        if i == 0:
            chunks.append(sec.strip()) # Usually the H1 title and intro
        else:
            chunks.append("## " + sec.strip()) # Re-attach the H2 marker
    return chunks

documents = []
metadatas = []
ids = []

print("Reading and chunking corpus files...")
for filepath in Path("corpus").rglob("*.md"):
    text = filepath.read_text(encoding="utf-8")
    chunks = chunk_markdown(text)

    # Infer basic graph metadata from the folder and file name
    folder_name = filepath.parent.name
    component_name = filepath.stem if folder_name == "components" else None

    for i, chunk in enumerate(chunks):
        documents.append(chunk)

        # Build metadata dictionary (Crucial for Context Graph filtering later)
        meta = {
            "source": filepath.name,
            "folder": folder_name,
            "chunk_index": i
        }
        if component_name:
            meta["component"] = component_name

        metadatas.append(meta)
        ids.append(f"{filepath.stem}_chunk_{i}")

print(f"Generated {len(documents)} chunks from the corpus.")

# 3. Generate Embeddings using Gemini
print("Calling Gemini API to generate embeddings...")
# For a large corpus, you would batch this. Since our corpus is small, one call is fine.
response = gemini_client.models.embed_content(
    model='gemini-embedding-001',
    contents=documents,
    # config=types.EmbedContentConfig(output_dimensionality=768) # Optional
)

# Extract the embedding vectors from the response
embeddings = [e.values for e in response.embeddings]

# 4. Ingest into ChromaDB
print("Inserting data into ChromaDB...")
collection.upsert(
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas,
    ids=ids
)

print(f"\nSuccess! ChromaDB collection now contains {collection.count()} items.")
print("Database saved to the './chroma_db' directory.")
