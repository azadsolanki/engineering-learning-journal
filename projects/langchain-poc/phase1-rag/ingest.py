"""
Phase 1 - Step 1: Ingest and embed docs into ChromaDB.

Loads all markdown files from the fedora-engineering-workstation docs,
splits them into chunks, embeds using Ollama, and stores in ChromaDB.

Usage:
    python ingest.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

load_dotenv()

DOCS_PATH = os.getenv("DOCS_PATH", "../../learning/fedora-engineering-workstation/docs")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHROMA_DIR = "./chroma_db"


def ingest():
    docs_path = Path(DOCS_PATH).expanduser().resolve()
    print(f"Loading docs from: {docs_path}")

    # Load all markdown files
    loader = DirectoryLoader(
        str(docs_path),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    docs = loader.load()
    print(f"Loaded {len(docs)} documents")

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(docs)
    print(f"Split into {len(chunks)} chunks")

    # Embed and store
    print(f"Embedding with {EMBED_MODEL} via Ollama...")
    embeddings = OllamaEmbeddings(
        model=EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
    )

    print(f"Stored {len(chunks)} chunks in ChromaDB at {CHROMA_DIR}")
    return vectorstore


if __name__ == "__main__":
    ingest()
