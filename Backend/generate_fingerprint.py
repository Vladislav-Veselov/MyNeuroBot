# generate_fingerprint.py
#!/usr/bin/env python3
import json
import hashlib
from pathlib import Path

# adjust this path to wherever your knowledge.txt lives
KNOWLEDGE_FILE = Path(r"C:\PARTNERS\NeuroBot\Backend\knowledge.txt")
FINGERPRINT_FILE = Path(__file__).parent / "last_fingerprint.json"

def compute_document_hash(content: str) -> str:
    """Compute a SHA-256 hash for a document block."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def split_qa_pairs(text: str):
    """Split the raw text into separate Q&A blocks."""
    pairs = []
    current = []
    for line in text.splitlines():
        if line.startswith("Вопрос:") and current:
            pairs.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        pairs.append("\n".join(current))
    return pairs

def main():
    txt = KNOWLEDGE_FILE.read_text(encoding="utf-8")
    pairs = split_qa_pairs(txt)

    fingerprint = {}
    for block in pairs:
        # extract the question line after "Вопрос:"
        if "Вопрос:" in block:
            question = block.split("Вопрос:")[1].splitlines()[0].strip()
            fingerprint[question] = compute_document_hash(block)

    FINGERPRINT_FILE.write_text(
        json.dumps(fingerprint, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"Fingerprint generated with {len(fingerprint)} entries → {FINGERPRINT_FILE}")

if __name__ == "__main__":
    main()
