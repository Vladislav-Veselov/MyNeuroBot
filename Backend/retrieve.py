"""
query_vector_store.py
CLI helper to test a local FAISS vector store built with LangChain.
-------------------------------------------------------------------
Usage:
    $ export OPENAI_API_KEY="sk-..."        # or keep it in a .env file
    $ python query_vector_store.py
    >> What are the core features of product X?
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_DIR = BASE_DIR / "user_data" / "admin" / "vector_KB"  # <- your index
EMBED_MODEL = "text-embedding-3-large"
TOP_K = 5                         # how many results to show

# ── 2. Load vector store ─────────────────────────────────────────
#   allow_dangerous_deserialization=True is required by LangChain ≥0.2.x
#   because FAISS indices are pickled.
embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
store = FAISS.load_local(
    str(VECTOR_DIR),
    embeddings,
    allow_dangerous_deserialization=True,
)

print(f"Loaded FAISS store from {VECTOR_DIR.resolve()}")
print("Type a question (or 'quit' to exit)…\n")

# ── 3. Simple REPL for ad-hoc testing ────────────────────────────
while True:
    query = input(">> ").strip()
    if query.lower() in {"quit", "exit"}:
        break
    if not query:
        continue

    # similarity_search_with_score returns (Document, distance) pairs
    docs_and_scores = store.similarity_search_with_score(query, k=TOP_K)

    if not docs_and_scores:
        print("⚠️  No matches found.\n")
        continue

    print(f"\nTop {len(docs_and_scores)} matches:\n")
    for rank, (doc, score) in enumerate(docs_and_scores, start=1):
        print(f"#{rank}  (distance={score:.3f})")
        print(doc.page_content)      # first 500 chars
        if doc.metadata:
            print(f"  metadata: {doc.metadata}")
        print("-" * 60)
    print()  # blank line between queries
