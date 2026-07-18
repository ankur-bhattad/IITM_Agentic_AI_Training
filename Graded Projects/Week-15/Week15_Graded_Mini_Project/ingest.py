"""
ingest.py
---------
Document ingestion and indexing pipeline for the E-Commerce Domain Support Assistant.

Source documents are real, publicly available Amazon.in Customer Service help
pages (saved as PDF), covering: Returns Policy, Shipping & Delivery, Warranty FAQs,
and Payment Issues. See README.md for the original source links.

What this does:
1. Loads all PDF documents from the local `documents/` folder
2. Splits them into semantic chunks
3. Generates embeddings using OpenAI embeddings
4. Stores the embeddings in a FAISS vector store, persisted to disk

Run this once (or whenever the documents folder changes) before running chatbot.py / app.py.
"""

import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Load OPENAI_API_KEY (and any other vars) from a local .env file, if present.
# Falls back silently to already-set environment variables if no .env exists.
load_dotenv()

# -----------------------------------------
# Configuration
# -----------------------------------------
DATA_FOLDER = "documents"
VECTOR_STORE = "ecommerce_vector_db"
EMBEDDING_MODEL = "text-embedding-3-small"

CHUNK_SIZE = 600
CHUNK_OVERLAP = 50

# Vocareum-issued keys (starting with "voc-") are proxied through Vocareum's own
# gateway, not api.openai.com. If OPENAI_API_BASE is set in .env, it's passed
# through here; otherwise the OpenAI SDK default endpoint is used.
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE")


def ingest():
    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentError(
            "OPENAI_API_KEY environment variable is not set. "
            "Set it before running ingestion (never hard-code it in source files)."
        )

    # 1) Document Ingestion: load all PDF files from the documents folder
    print(f"Loading documents from '{DATA_FOLDER}'...")
    loader = DirectoryLoader(
        path=DATA_FOLDER,
        glob="./*.pdf",
        loader_cls=PyMuPDFLoader,
        use_multithreading=True,
        show_progress=True,
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} page(s) across all PDFs.")

    # 2) Split content into semantic chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "(?<=\\. )", " ", ""],
    )
    splitted_text = text_splitter.split_documents(documents)
    print(f"Split into {len(splitted_text)} chunks.")

    # 3) Generate embeddings using OpenAI embeddings
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OPENAI_API_BASE,  # None uses the default api.openai.com endpoint
    )

    # 4) Store embeddings in a FAISS vector store
    print("Building FAISS index...")
    try:
        vectordb = FAISS.from_documents(
            documents=splitted_text,
            embedding=embeddings,
        )
    except Exception as e:
        if "AuthenticationError" in type(e).__name__ or "invalid_api_key" in str(e):
            raise RuntimeError(
                "OpenAI authentication failed. If you're using a Vocareum-issued key "
                "(starts with 'voc-'), it requires a custom OPENAI_API_BASE endpoint — "
                "set it in .env (see the comment in .env.example) using the URL from "
                "your Vocareum_GenAI_API_Students_Guide.pdf. If you're using a real "
                "OpenAI key, double-check it hasn't been truncated or expired."
            ) from e
        raise

    # Persist to disk so chatbot.py / app.py can load it without re-embedding
    vectordb.save_local(VECTOR_STORE)
    print(f"Vector store saved to '{VECTOR_STORE}'.")


if __name__ == "__main__":
    ingest()
