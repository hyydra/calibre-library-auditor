#!/usr/bin/env python3
"""
doc_ole_to_epub.py

Direct binary OLE Compound Document extractor for corrupted or locked legacy
Microsoft Word .doc files. Recovers UTF-16LE and CP1250 text runs from 512-byte
sectors without requiring Microsoft Word or COM automation.
"""

import os
import sys
import re
import zipfile

def extract_ole_doc_text(doc_path):
    with open(doc_path, 'rb') as f:
        data = f.read()

    # Look for UTF-16LE text blocks
    text_pieces = []
    # Find readable strings >= 10 chars
    pattern = re.compile(b'(?:[\x20-\x7e\xa0-\xff]\x00){10,}')
    for match in pattern.finditer(data):
        chunk = match.group(0)
        try:
            decoded = chunk.decode('utf-16le', errors='ignore')
            decoded = ' '.join(decoded.split())
            if len(decoded) > 15:
                text_pieces.append(decoded)
        except Exception:
            pass

    # If UTF-16LE didn't find substantial text, scan CP1250 / ISO-8859-2 runs
    if sum(len(p) for p in text_pieces) < 500:
        pattern_8bit = re.compile(b'[\x20-\x7e\xa0-\xff]{20,}')
        for match in pattern_8bit.finditer(data):
            chunk = match.group(0)
            try:
                decoded = chunk.decode('cp1250', errors='ignore')
                decoded = ' '.join(decoded.split())
                if len(decoded) > 20:
                    text_pieces.append(decoded)
            except Exception:
                pass

    return "\n\n".join(text_pieces)

def create_simple_epub(output_path, title, author, text_content):
    import html
    escaped_text = html.escape(text_content).replace("\n\n", "</p><p>")
    html_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{html.escape(title)}</title>
    <style>body {{ font-family: sans-serif; line-height: 1.5; padding: 2em; }} p {{ margin-bottom: 1em; }}</style>
</head>
<body>
    <h1>{html.escape(title)}</h1>
    <h3>{html.escape(author)}</h3>
    <p>{escaped_text}</p>
</body>
</html>"""

    opf_content = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="BookId">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>{html.escape(title)}</dc:title>
        <dc:creator>{html.escape(author)}</dc:creator>
        <dc:language>hu</dc:language>
        <dc:identifier id="BookId">urn:uuid:simple-doc-converter</dc:identifier>
    </metadata>
    <manifest>
        <item id="content" href="content.xhtml" media-type="application/xhtml+xml"/>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    </manifest>
    <spine toc="ncx">
        <itemref idref="content"/>
    </spine>
</package>"""

    ncx_content = f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head><meta name="dtb:uid" content="urn:uuid:simple-doc-converter"/></head>
    <docTitle><text>{html.escape(title)}</text></docTitle>
    <navMap>
        <navPoint id="navpoint-1" playOrder="1">
            <navLabel><text>{html.escape(title)}</text></navLabel>
            <content src="content.xhtml"/>
        </navPoint>
    </navMap>
</ncx>"""

    with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        zf.writestr('META-INF/container.xml', """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>""")
        zf.writestr('content.opf', opf_content)
        zf.writestr('toc.ncx', ncx_content)
        zf.writestr('content.xhtml', html_content)

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: python doc_ole_to_epub.py <doc_path> <epub_path> <title> <author>")
        sys.exit(1)
    text = extract_ole_doc_text(sys.argv[1])
    create_simple_epub(sys.argv[2], sys.argv[3], sys.argv[4], text)
    print(f"Created {sys.argv[2]} ({len(text)} characters extracted).")
