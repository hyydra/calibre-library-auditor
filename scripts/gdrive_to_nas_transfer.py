#!/usr/bin/env python3
"""
gdrive_to_nas_transfer.py

High-performance multithreaded mirror of EPUB files from Google Drive virtual drive
(DriveFS) to a local network storage / Synology NAS destination with resume capability,
per-file progress tracking, and error isolation.
"""

import os
import sys
import time
import shutil
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')

def process_file(src, dst_root):
    try:
        # Strip drive prefix (e.g. G:\)
        if len(src) >= 3 and src[1:3] in (':\\', ':/'):
            rel = src[3:]
        else:
            rel = src.lstrip('\\/')

        dst = os.path.join(dst_root, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        src_sz = os.path.getsize(src)
        if os.path.exists(dst) and os.path.getsize(dst) == src_sz:
            return 'skipped', src_sz, None

        shutil.copy2(src, dst)
        return 'copied', src_sz, None
    except Exception as e:
        return 'error', 0, str(e)

def transfer_epubs(list_file, dest_root, workers=12):
    if not os.path.exists(list_file):
        print(f"Error: List file {list_file} not found.")
        return

    with open(list_file, 'r', encoding='utf-8', errors='replace') as f:
        src_files = [l.strip() for l in f if l.strip()]

    total = len(src_files)
    print(f"Total files to transfer: {total}")
    print(f"Destination root:        {dest_root}")
    print(f"Concurrency workers:     {workers}")

    copied = 0
    skipped = 0
    errors = 0
    bytes_copied = 0

    t0 = time.time()
    last_log = t0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_file, p, dest_root): p for p in src_files}
        done = 0
        for fut in as_completed(futures):
            done += 1
            status, sz, err = fut.result()
            if status == 'copied':
                copied += 1
                bytes_copied += sz
            elif status == 'skipped':
                skipped += 1
            elif status == 'error':
                errors += 1

            now = time.time()
            if done % 100 == 0 or done == total or (now - last_log) >= 15:
                pct = (done / total) * 100
                mb = bytes_copied / (1024 * 1024)
                rate = mb / max(now - t0, 0.001)
                print(f"[{done:4d}/{total}] {pct:5.1f}% | Copied: {copied} ({mb:.1f} MB) | Skipped: {skipped} | Errors: {errors} | Speed: {rate:.2f} MB/s")
                last_log = now

    print(f"\nFinished in {time.time() - t0:.1f}s. Copied: {copied}, Skipped: {skipped}, Errors: {errors}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Transfer EPUBs from cloud to NAS.")
    parser.add_argument("--list", default=r"L:\calibre\gdrive_epubs_list.txt", help="Path to text file containing file paths")
    parser.add_argument("--dest", default=r"W:\backup\google_drive_epubs", help="Destination root path on NAS")
    parser.add_argument("--workers", type=int, default=12, help="Number of concurrent copy threads")
    args = parser.parse_args()
    transfer_epubs(args.list, args.dest, args.workers)
