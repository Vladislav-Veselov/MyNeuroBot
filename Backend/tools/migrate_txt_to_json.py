#!/usr/bin/env python3
import json
from pathlib import Path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from vectorize import split_qa_pairs, extract_question  # reuse existing helpers

def parse_txt_to_pairs(txt: str):
    pairs = []
    for blk in split_qa_pairs(txt):
        if "Вопрос:" not in blk:
            continue
        q = extract_question(blk)
        lines = blk.splitlines()
        hdr = next((i for i,l in enumerate(lines) if l.startswith("Вопрос:")), None)
        a = "\n".join(lines[hdr+1:]).strip() if hdr is not None and hdr+1 < len(lines) else ""
        pairs.append({"question": q, "answer": a})
    return pairs

def migrate_kb(kb_dir: Path):
    txt = kb_dir / "knowledge.txt"
    jsn = kb_dir / "knowledge.json"
    if not txt.exists():
        return
    content = txt.read_text(encoding="utf-8")
    data = parse_txt_to_pairs(content)
    jsn.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Migrated {txt} → {jsn} ({len(data)} items)")

if __name__ == "__main__":
    base = Path("user_data")  # adjust if needed
    for user_dir in base.iterdir():
        kb_root = user_dir / "knowledge_bases"
        if not kb_root.exists(): 
            continue
        for kb in kb_root.iterdir():
            if kb.is_dir():
                migrate_kb(kb)
