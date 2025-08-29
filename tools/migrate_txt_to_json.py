#!/usr/bin/env python3
"""
Migration script to convert knowledge.txt files to knowledge.json format.
Run this from the root directory (NeuroBot) to migrate all knowledge bases.
"""

import json
from pathlib import Path
import sys
import os


from pathlib import Path
project_root = Path(__file__).resolve().parents[1]  # …/NeuroBot
sys.path.insert(0, str(project_root / "Backend"))

try:
    from vectorize import split_qa_pairs, extract_question  # reuse existing helpers
except ImportError:
    print("❌ Error: Could not import vectorize module")
    print("💡 Make sure you're running from the NeuroBot root directory")
    print("   Current working directory:", os.getcwd())
    print("   Backend directory exists:", os.path.exists("Backend"))
    sys.exit(1)

def parse_txt_to_pairs(txt: str):
    """Parse text content into Q&A pairs"""
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
    """Migrate a single knowledge base from txt to json"""
    txt = kb_dir / "knowledge.txt"
    jsn = kb_dir / "knowledge.json"
    
    if not txt.exists():
        print(f"  ⚠️  No knowledge.txt found in {kb_dir.name}")
        return False
        
    try:
        content = txt.read_text(encoding="utf-8")
        data = parse_txt_to_pairs(content)
        
        # Write JSON file
        jsn.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        
        print(f"  ✅ Migrated {txt.name} → {jsn.name} ({len(data)} items)")
        return True
        
    except Exception as e:
        print(f"  ❌ Error migrating {kb_dir.name}: {str(e)}")
        return False

def main():
    """Main migration function"""
    print("🔄 NeuroBot Knowledge File Migration: TXT → JSON")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("Backend").exists():
        print("❌ Error: Please run this script from the NeuroBot root directory")
        print("   python tools/migrate_txt_to_json.py")
        return 1
        
    base = Path("user_data")
    if not base.exists():
        print("❌ Error: user_data directory not found")
        return 1
        
    print(f"📁 Scanning {base} for knowledge bases...")
    
    migrated_count = 0
    total_kbs = 0
    
    # Iterate through all user directories
    for user_dir in base.iterdir():
        if not user_dir.is_dir():
            continue
            
        kb_root = user_dir / "knowledge_bases"
        if not kb_root.exists():
            continue
            
        print(f"\n👤 User: {user_dir.name}")
        
        # Iterate through knowledge bases
        for kb in kb_root.iterdir():
            if not kb.is_dir():
                continue
                
            total_kbs += 1
            print(f"  📚 KB: {kb.name}")
            
            if migrate_kb(kb):
                migrated_count += 1
    
    print("\n" + "=" * 60)
    print("📊 Migration Summary")
    print("=" * 60)
    print(f"Total Knowledge Bases: {total_kbs}")
    print(f"Successfully Migrated: {migrated_count}")
    print(f"Failed: {total_kbs - migrated_count}")
    
    if migrated_count > 0:
        print(f"\n✅ Migration completed successfully!")
        print("💡 Next steps:")
        print("  1. Test the system with: cd Backend && python test_simple.py")
        print("  2. Run comprehensive tests: cd Backend && python run_all_tests.py")
        print("  3. Consider removing old knowledge.txt files after verification")
    else:
        print(f"\n⚠️  No knowledge bases were migrated")
        print("💡 This might be normal if:")
        print("  - No knowledge.txt files exist")
        print("  - All knowledge bases are already in JSON format")
        print("  - No users have knowledge bases yet")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
