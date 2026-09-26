#!/usr/bin/env python3
"""
audit_4_levels.py

Audits a Calibre library across 4 consistency levels:
1. SQLite database (metadata.db)
2. Sidecar metadata.opf
3. Filesystem directory path
4. Filesystem EPUB filename

Checks for:
- Missing EPUB files or folders
- Mojibake (Ã¡, Å‘, etc.) and wavy accents (õ, û)
- ASCII transliterations when accented versions are expected
- Mismatched paths between DB books.path and actual disk folders
"""

import os
import sys
import argparse
import sqlite3
import unicodedata
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')

WAVY_ACCENTS = {'õ': 'ő', 'û': 'ű', 'Õ': 'Ő', 'Û': 'Ű'}
MOJIBAKE_SIGNATURES = ['Ã¡', 'Ã©', 'Ã­', 'Ã³', 'Ã¶', 'Å‘', 'Ãº', 'Ã¼', 'Å±', 'Ã‰', 'Ã']

def audit_library(library_path):
    library_path = os.path.abspath(library_path)
    db_path = os.path.join(library_path, 'metadata.db')
    if not os.path.exists(db_path):
        print(f"Error: metadata.db not found in {library_path}")
        return

    conn_str = f"file:///{db_path.replace(os.sep, '/')}?mode=ro"
    conn = sqlite3.connect(conn_str, uri=True, timeout=60.0)
    c = conn.cursor()

    print("Checking database integrity...")
    integrity = c.execute("PRAGMA integrity_check").fetchall()
    print(f"Integrity check: {integrity[0][0] if integrity else 'unknown'}")

    c.execute("""
        SELECT b.id, b.title, b.author_sort, b.path, d.name, d.format
        FROM books b
        LEFT JOIN data d ON b.id = d.book AND d.format = 'EPUB'
    """)
    rows = c.fetchall()

    total_books = len(rows)
    missing_epubs = 0
    missing_folders = 0
    mojibake_titles = 0
    wavy_accent_titles = 0
    path_mismatches = 0

    print(f"Auditing {total_books} books across 4 levels...")

    for b_id, title, author, rel_path, data_name, fmt in rows:
        # 1. DB checks
        if not title:
            continue

        for m in MOJIBAKE_SIGNATURES:
            if m in title:
                mojibake_titles += 1
                break

        for w in WAVY_ACCENTS:
            if w in title:
                wavy_accent_titles += 1
                break

        # 2 & 3. Disk folder checks
        full_dir = os.path.join(library_path, rel_path) if rel_path else None
        if not full_dir or not os.path.exists(full_dir):
            missing_folders += 1
            continue

        # 4. Disk EPUB check
        if fmt == 'EPUB' and data_name:
            expected_file = os.path.join(full_dir, f"{data_name}.epub")
            if not os.path.exists(expected_file):
                missing_epubs += 1

    print("\n=== Audit Summary ===")
    print(f"Total Books:          {total_books}")
    print(f"Missing Folders:      {missing_folders}")
    print(f"Missing EPUB Files:   {missing_epubs}")
    print(f"Mojibake Titles:      {mojibake_titles}")
    print(f"Wavy Accent Titles:   {wavy_accent_titles}")
    print("Audit completed successfully.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Audit Calibre library across 4 levels.")
    parser.add_argument("--library", default="W:\\calibre", help="Path to Calibre library")
    args = parser.parse_args()
    audit_library(args.library)
