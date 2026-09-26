#!/usr/bin/env python3
"""
inspect_book_content.py

Opens an EPUB file, inspects internal metadata (OPF) and spine HTML documents
to discover the true author, title, and Hungarian orthography.
"""

import os
import sys
import re
import zipfile
import xml.etree.ElementTree as ET

def clean_html_text(html):
    text = re.sub(r'<[^>]+>', ' ', html)
    text = ' '.join(text.split())
    return text

def inspect_epub(epub_path):
    if not os.path.exists(epub_path):
        return {"error": "File does not exist"}

    result = {
        "path": epub_path,
        "opf_title": None,
        "opf_creator": None,
        "opf_language": None,
        "first_text_sample": None,
        "valid": False
    }

    try:
        with zipfile.ZipFile(epub_path, 'r') as zf:
            result["valid"] = True
            opf_names = [n for n in zf.namelist() if n.endswith('.opf')]
            if opf_names:
                opf_data = zf.read(opf_names[0])
                root = ET.fromstring(opf_data)
                ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
                titles = [e.text for e in root.findall('.//dc:title', ns) if e.text]
                creators = [e.text for e in root.findall('.//dc:creator', ns) if e.text]
                languages = [e.text for e in root.findall('.//dc:language', ns) if e.text]
                result["opf_title"] = titles[0] if titles else None
                result["opf_creator"] = creators[0] if creators else None
                result["opf_language"] = languages[0] if languages else None

            # Read text samples from spine HTML files
            html_files = [n for n in zf.namelist() if n.endswith(('.html', '.xhtml', '.htm'))]
            for hf in html_files[:3]:
                raw = zf.read(hf).decode('utf-8', errors='replace')
                cleaned = clean_html_text(raw)
                if len(cleaned) > 20:
                    result["first_text_sample"] = cleaned[:250]
                    break
    except Exception as e:
        result["error"] = str(e)

    return result

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python inspect_book_content.py <path_to_epub>")
        sys.exit(1)
    res = inspect_epub(sys.argv[1])
    for k, v in res.items():
        print(f"{k}: {v}")
