"""
Reassemble the split SQLite database file.

The insurance_portal.db file was split into parts to comply with GitHub's
25MB file size limit. Run this script after cloning to reconstruct the
original database.

Usage:
    python scripts/reassemble_db.py
"""

import os
import sys

def reassemble_database():
    """Reassemble insurance_portal.db from split parts."""
    db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'data', 'synthetic')
    db_path = os.path.join(db_dir, 'insurance_portal.db')
    
    # Check if already assembled
    if os.path.exists(db_path):
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"[INFO] insurance_portal.db already exists ({size_mb:.1f} MB)")
        response = input("Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("[SKIP] Keeping existing database.")
            return
    
    # Find all parts
    parts = sorted([
        f for f in os.listdir(db_dir)
        if f.startswith('insurance_portal.db.part')
    ])
    
    if not parts:
        print("[ERROR] No split parts found in data/synthetic/")
        print("        Expected files like: insurance_portal.db.part1, insurance_portal.db.part2, ...")
        sys.exit(1)
    
    print(f"[INFO] Found {len(parts)} parts to reassemble:")
    for part in parts:
        part_path = os.path.join(db_dir, part)
        size_mb = os.path.getsize(part_path) / (1024 * 1024)
        print(f"       {part} ({size_mb:.1f} MB)")
    
    # Reassemble
    print(f"\n[REASSEMBLING] -> {db_path}")
    with open(db_path, 'wb') as outfile:
        for part in parts:
            part_path = os.path.join(db_dir, part)
            with open(part_path, 'rb') as infile:
                while True:
                    chunk = infile.read(8192)
                    if not chunk:
                        break
                    outfile.write(chunk)
    
    final_size = os.path.getsize(db_path) / (1024 * 1024)
    print(f"[SUCCESS] Reassembled insurance_portal.db ({final_size:.1f} MB)")
    print(f"[INFO] You can now safely delete the .part files if desired.")

if __name__ == '__main__':
    reassemble_database()
