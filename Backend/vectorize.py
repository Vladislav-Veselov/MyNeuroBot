#!/usr/bin/env python3
import json
import hashlib
import uuid
from pathlib import Path
import os
from dotenv import load_dotenv

import numpy as np
import faiss
from langchain_openai import OpenAIEmbeddings

# ─── CONFIG ─────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
UUID_NAMESPACE = uuid.NAMESPACE_URL

# ─── HELPERS ────────────────────────────────────────────────────────────────────

def compute_document_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def split_qa_pairs(text: str):
    pairs, current = [], []
    for line in text.splitlines():
        if line.startswith("Вопрос:") and current:
            pairs.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        pairs.append("\n".join(current))
    return pairs

def extract_question(block: str) -> str:
    return block.split("Вопрос:")[1].splitlines()[0].strip()

def make_id(question: str) -> int:
    u = uuid.uuid5(UUID_NAMESPACE, question)
    return u.int & ((1 << 63) - 1)

# ─── MAIN ────────────────────────────────────────────────────────────────────────

def main():
    # 1) Load .env and ensure OPENAI_API_KEY is set
    load_dotenv(override=True)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY not found in .env file.")
    os.environ["OPENAI_API_KEY"] = api_key

    # 2) Get user-specific paths
    try:
        from auth import get_current_user_data_dir
        user_data_dir = get_current_user_data_dir()
    except Exception as e:
        print(f"Error getting user data directory: {str(e)}")
        return False

    # Get current KB ID
    try:
        from app.blueprints.kb_api import get_current_kb_id
        current_kb_id = get_current_kb_id()
    except Exception as e:
        print(f"Error getting current KB ID: {str(e)}")
        return False

def main_with_context(user_data_dir: str, current_kb_id: str):
    """Main function that works with explicit user and KB context."""
    # 1) Load .env and ensure OPENAI_API_KEY is set
    load_dotenv(override=True)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY not found in .env file.")
    os.environ["OPENAI_API_KEY"] = api_key

    # 2) Use provided user and KB context
    user_data_dir = Path(user_data_dir)
    current_kb_id = str(current_kb_id)

    KNOWLEDGE_FILE = user_data_dir / "knowledge_bases" / current_kb_id / "knowledge.txt"
    FINGERPRINT_FILE = user_data_dir / "knowledge_bases" / current_kb_id / "last_fingerprint.json"
    VECTOR_STORE_DIR = user_data_dir / "knowledge_bases" / current_kb_id / "vector_KB"
    INDEX_FILE = VECTOR_STORE_DIR / "index.faiss"
    DOCSTORE_FILE = VECTOR_STORE_DIR / "docstore.json"

    # 3) Prepare directories
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

    # 4) Load previous fingerprint
    if FINGERPRINT_FILE.exists():
        old_fp = json.loads(FINGERPRINT_FILE.read_text(encoding="utf-8"))
    else:
        old_fp = {}

    # 5) Read & hash current Q&A
    txt = KNOWLEDGE_FILE.read_text(encoding="utf-8")
    blocks = split_qa_pairs(txt)

    new_fp = {}
    q2block = {}
    for blk in blocks:
        if "Вопрос:" not in blk:
            continue
        q = extract_question(blk)
        h = compute_document_hash(blk)
        new_fp[q] = h
        q2block[q] = blk

    old_qs = set(old_fp)
    new_qs = set(new_fp)

    removed = old_qs - new_qs
    added   = new_qs - old_qs
    changed = {q for q in new_qs & old_qs if old_fp[q] != new_fp[q]}

    print(f"Removed {len(removed)}, Added {len(added)}, Changed {len(changed)}")
    if not (removed or added or changed):
        print("No changes. Vector store is up-to-date.")
        return

    # 5) Initialize embeddings & FAISS index
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    print(f"Index file exists: {INDEX_FILE.exists()}")
    print(f"Index file path: {INDEX_FILE}")
    print(f"Index file absolute path: {INDEX_FILE.absolute()}")
    
    if not INDEX_FILE.exists():
        print("Creating new FAISS index")
        dim = len(embeddings.embed_query("test"))
        index = faiss.IndexIDMap(faiss.IndexFlatL2(dim))
        docstore = {}
    else:
        print("Reading existing FAISS index")
        index = faiss.read_index(str(INDEX_FILE))
        docstore = json.loads(DOCSTORE_FILE.read_text(encoding="utf-8"))

    # 6) Remove deleted 
    to_remove = removed | changed
    if to_remove:
        ids_to_rm = [make_id(q) for q in to_remove if str(make_id(q)) in docstore]
        if ids_to_rm:
            index.remove_ids(np.array(ids_to_rm, dtype="int64"))
            for q in to_remove:
                docstore.pop(str(make_id(q)), None)
            print(f"  → removed {len(ids_to_rm)} vectors")

    # 7) Upsert added + changed
    upsert = list(added | changed)
    if upsert:
        texts = [q2block[q] for q in upsert]
        vectors = embeddings.embed_documents(texts)
        ids = [make_id(q) for q in upsert]

        arr = np.array(vectors, dtype="float32")
        index.add_with_ids(arr, np.array(ids, dtype="int64"))

        for q, idx in zip(upsert, ids):
            docstore[str(idx)] = q
        print(f"  → upserted {len(upsert)} vectors")

    # 8) Persist everything
    try:
        print(f"Writing FAISS index to: {INDEX_FILE}")
        print(f"Index file parent exists: {INDEX_FILE.parent.exists()}")
        print(f"Index file parent is dir: {INDEX_FILE.parent.is_dir()}")
        
        # Ensure the directory exists
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to absolute path and normalize for Windows
        index_path = str(INDEX_FILE.absolute().resolve())
        print(f"Normalized index path: {index_path}")
        
        # Try to create the file first to avoid FAISS Windows issues
        try:
            with open(index_path, 'wb') as f:
                f.write(b'')  # Create empty file
            print("Empty index file created successfully")
        except Exception as e:
            print(f"Warning: Could not create empty file: {e}")
        
        # Use temporary file approach to avoid FAISS Windows path issues
        import tempfile
        import shutil
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.faiss', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        print(f"Using temporary file: {temp_path}")
        
        try:
            faiss.write_index(index, temp_path)
            print("FAISS index written to temp file successfully")
            
            # Move the file to the final location
            shutil.move(temp_path, index_path)
            print("FAISS index moved to final location successfully")
        except Exception as e:
            print(f"Error with temp file approach: {e}")
            # Fallback to direct writing
            faiss.write_index(index, index_path)
        print("FAISS index written successfully")
        
        print(f"Writing docstore to: {DOCSTORE_FILE}")
        with open(DOCSTORE_FILE, "w", encoding="utf-8") as f:
            json.dump(docstore, f, ensure_ascii=False, indent=2)
        print("Docstore written successfully")
        
        print(f"Writing fingerprint to: {FINGERPRINT_FILE}")
        FINGERPRINT_FILE.write_text(
            json.dumps(new_fp, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print("Fingerprint written successfully")
        
        print("Done. Index and fingerprint updated.")
    except Exception as e:
        print(f"Error during file writing: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise

def rebuild_vector_store():
    """Rebuild the vector store from the knowledge file. This function can be imported and called from other modules."""
    try:
        main()
        return True
    except Exception as e:
        print(f"Error rebuilding vector store: {str(e)}")
        return False

def rebuild_vector_store_with_context(user_data_dir: str, current_kb_id: str):
    """Rebuild the vector store with explicit user and KB context. This avoids Flask context issues."""
    try:
        # Set environment variables for the vectorization process
        import os
        os.environ['USER_DATA_DIR'] = user_data_dir
        os.environ['CURRENT_KB_ID'] = current_kb_id
        
        # Call the main function with context
        main_with_context(user_data_dir, current_kb_id)
        return True
    except Exception as e:
        print(f"Error rebuilding vector store with context: {str(e)}")
        return False

if __name__ == "__main__":
    main()
