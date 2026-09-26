#!/usr/bin/env python3
"""
reconcile_gdrive.py

Recursively scans Google Drive paths for EPUB files, normalizes titles,
deduplicates against the active Calibre library, and reports candidate books
ready for staging and import.
"""

import os
import sys
import re
import sqlite3
import unicodedata

def normalize_title(s):
    if not s:
        return ''
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]', '', s.lower())

def reconcile_with_calibre(gdrive_list_file, library_path):
    db_path = os.path.join(library_path, 'metadata.db')
    conn = sqlite3.connect(f"file:///{db_path.replace(os.sep, '/')}?mode=ro", uri=True, timeout=60.0)
    c = conn.cursor()

    c.execute("SELECT id, title FROM books")
    library_books = c.fetchall()
    conn.close()

    known_ids = {row[0] for row in library_books}
    known_titles = {normalize_title(row[1]) for row in library_books if row[1]}

    with open(gdrive_list_file, 'r', encoding='utf-8', errors='replace') as f:
        paths = [l.strip() for l in f if l.strip()]

    id_regex = re.compile(r'\((\d+)\)[\\/]')
    matched = 0
    new_candidates = []

    for p in paths:
        m = id_regex.search(p)
        if m and int(m.group(1)) in known_ids:
            matched += 1
            continue

        fname = os.path.splitext(os.path.basename(p))[0]
        n_fname = normalize_title(fname)

        is_known = any(kt and (kt in n_fname or n_fname in kt) for kt in known_titles)
        if is_known:
            matched += 1
        else:
            new_candidates.append(p)

    print(f"Total Cloud Files:     {len(paths)}")
    print(f"Matched Existing:      {matched}")
    print(f"New Unique Candidates: {len(new_candidates)}")
    for cand in new_candidates[:10]:
        print(f"  Candidate: {cand}")

if __name__ == '__main__':
    list_file = sys.argv[1] if len(sys.argv) > 1 else 'L:\\calibre\\gdrive_epubs_list.txt'
    lib = sys.argv[2] if len(sys.argv) > 2 else 'W:\\calibre'
    reconcile_with_calibre(list_file, lib)
