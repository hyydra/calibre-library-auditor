# Calibre Library Auditor & Accent Pipeline

Production audit, standardization, and accent synchronization pipeline for Calibre ebook libraries, maintaining 100% valid EPUB format and authentic Hungarian orthography (`á, é, í, ó, ö, ő, ú, ü, ű`) across all four tiers:

1. **Database:** SQLite (`metadata.db`) `books.title`, `authors.name`, `books.path`, `data.name`.
2. **Sidecar OPF:** `metadata.opf` Dublin Core metadata tags.
3. **Filesystem Directory:** `<Author>/<Title (id)>/`.
4. **Filesystem Filename:** `<Title> - <Author>.epub`.

## Features
- **4-Level Audit & Verification:** Checks complete consistency between database records, sidecars, folder names, and EPUB files.
- **Hungarian Accent Preservation:** Completely overrides Calibre's native ASCII transliteration to keep real Hungarian characters on disk.
- **Internal Spine Inspection:** Inspects EPUB title pages and chapter contents to detect true authors and titles, eliminating scraper garbage and hash stubs.
- **Damaged Word .DOC OLE Recovery:** Pure-Python sector extractor recovering text from corrupt or blocked Word files without Microsoft Office.
- **Cloud Deduplication & Reconciliation:** Scans Google Drive and external backups, matching existing Calibre IDs and title hashes to ingest missing books without duplicates.

## Quick Start
```bash
# Audit active Calibre library
python scripts/audit_4_levels.py --library "W:\calibre"

# Inspect internal content of an EPUB
python scripts/inspect_book_content.py "path/to/book.epub"

# Scan Google Drive and match against library
python scripts/reconcile_gdrive.py "gdrive_list.txt" "W:\calibre"
```
