# generate_fingerprint.py
#!/usr/bin/env python3
import json
import hashlib
from pathlib import Path

# Use relative paths for production deployment
BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_FILE = BASE_DIR / "user_data" / "admin" / "knowledge.json"
FINGERPRINT_FILE = BASE_DIR / "user_data" / "admin" / "last_fingerprint.json"

def compute_document_hash(content: str) -> str:
    """Compute a SHA-256 hash for a document block."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()



def main():
    data = json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8")) if KNOWLEDGE_FILE.exists() else []
    
    fingerprint = {}
    for item in data:
        question = (item.get("question") or "").strip()
        answer = (item.get("answer") or "").strip()
        if question:
            # recreate the same "block" string used for embeddings/fingerprint
            block = f"Вопрос: {question}\n{answer}"
            fingerprint[question] = compute_document_hash(block)

    FINGERPRINT_FILE.write_text(
        json.dumps(fingerprint, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"Fingerprint generated with {len(fingerprint)} entries → {FINGERPRINT_FILE}")

if __name__ == "__main__":
    main()
