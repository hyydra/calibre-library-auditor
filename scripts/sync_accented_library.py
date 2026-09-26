#!/usr/bin/env python3
"""
sync_accented_library.py

Synchronizes Calibre database titles and authors to authentic Hungarian accented
filesystem paths (folders and filenames) while updating books.path and data.name.
"""

import os
import sys
import shutil
import sqlite3
import unicodedata
import xml.etree.ElementTree as ET

FORBIDDEN_FS_CHARS = '<>:"/\\|?*'

def sanitize_fs_name(s, max_len=120):
    if not s:
        return 'Unknown'
    cleaned = ''.join(c for c in s if c not in FORBIDDEN_FS_CHARS)
    cleaned = ' '.join(cleaned.split()).rstrip('. ')
    if not cleaned:
        return 'Unknown'
    return cleaned[:max_len].rstrip('. ')

def build_accented_paths(library_path):
    db_path = os.path.join(library_path, 'metadata.db')
    conn = sqlite3.connect(f"file:///{db_path.replace(os.sep, '/')}?mode=ro", uri=True, timeout=60.0)
    c = conn.cursor()

    c.execute("""
        SELECT b.id, b.title, a.name, b.path, d.name
        FROM books b
        LEFT JOIN books_authors_link bal ON b.id = bal.book
        LEFT JOIN authors a ON bal.author = a.id
        LEFT JOIN data d ON b.id = d.book AND d.format = 'EPUB'
        GROUP BY b.id
    """)
    rows = c.fetchall()
    conn.close()

    plan = []
    for b_id, title, author, cur_path, cur_data_name in rows:
        clean_author = sanitize_fs_name(author or 'Ismeretlen szerzo')
        clean_title = sanitize_fs_name(title or f'Konyv_{b_id}')

        new_folder_name = f"{clean_title} ({b_id})"
        new_rel_path = f"{clean_author}/{new_folder_name}"
        new_data_name = f"{clean_title} - {clean_author}"

        if cur_path != new_rel_path or cur_data_name != new_data_name:
            plan.append({
                "id": b_id,
                "cur_path": cur_path,
                "new_path": new_rel_path,
                "cur_data_name": cur_data_name,
                "new_data_name": new_data_name,
                "author": clean_author,
                "title": clean_title
            })

    return plan

if __name__ == '__main__':
    lib = sys.argv[1] if len(sys.argv) > 1 else 'W:\\calibre'
    plan = build_accented_paths(lib)
    print(f"Total books needing accented path synchronization: {len(plan)}")
