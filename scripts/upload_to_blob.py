#!/usr/bin/env python3
"""Upload all PDFs from data/ to Vercel Blob storage."""

import os
import sys
import json
import ipaddress
import socket
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Optional

# Load token from .env.local
def load_env():
    env_file = Path(__file__).parent.parent / ".env.local"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value:
                    os.environ.setdefault(key, value)

load_env()

BLOB_TOKEN = os.environ.get("BLOB_READ_WRITE_TOKEN", "")
DATA_DIR = Path(__file__).parent.parent / "data"
MANIFEST_FILE = Path(__file__).parent.parent / "blob_manifest.json"
ALLOWED_UPLOAD_HOSTS = {"blob.vercel-storage.com"}

if not BLOB_TOKEN:
    print("❌ BLOB_READ_WRITE_TOKEN not found in environment or .env.local")
    sys.exit(1)


def is_allowed_upload_url(url: str) -> bool:
    """Allow only HTTPS uploads to approved blob host."""
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return False

    if parsed.scheme != "https" or not parsed.hostname:
        return False

    hostname = parsed.hostname.lower()
    if hostname not in ALLOWED_UPLOAD_HOSTS:
        return False

    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False

    for _, _, _, _, sockaddr in addr_info:
        ip = ipaddress.ip_address(sockaddr[0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False

    return True


def upload_file(pdf_path: Path) -> Optional[dict]:
    """Upload a single PDF to Vercel Blob and return the URL."""
    filename = pdf_path.name
    
    with open(pdf_path, "rb") as f:
        data = f.read()
    
    # Vercel Blob API endpoint
    url = f"https://blob.vercel-storage.com/{filename}"
    if not is_allowed_upload_url(url):
        print(f"  ❌ Blocked non-allowlisted upload URL: {url}")
        return None
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {BLOB_TOKEN}",
            "Content-Type": "application/pdf",
            "x-api-version": "7",
        },
        method="PUT",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            return {
                "filename": filename,
                "url": result.get("url", ""),
                "size": len(data),
            }
    except urllib.error.HTTPError as e:
        print(f"  ❌ Failed {filename}: {e.code} {e.reason}")
        try:
            error_body = e.read().decode()
            print(f"     {error_body[:200]}")
        except (UnicodeDecodeError, OSError):
            print("     Unable to decode error body")
        return None
    except urllib.error.URLError as e:
        print(f"  ❌ Failed {filename}: {e.reason}")
        return None
    except OSError as e:
        print(f"  ❌ Failed {filename}: {e}")
        return None


def main():
    print("📤 Uploading PDFs to Vercel Blob Storage")
    print(f"   Source: {DATA_DIR}")
    print()
    
    # Load existing manifest to skip already uploaded files
    existing = {}
    if MANIFEST_FILE.exists():
        try:
            existing = json.loads(MANIFEST_FILE.read_text())
            print(f"📋 Found existing manifest with {len(existing)} entries")
        except (OSError, json.JSONDecodeError) as exc:
            print(f"⚠️ Failed to load existing manifest: {exc}")
    
    # Get all PDFs
    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    print(f"📂 Found {len(pdfs)} PDFs in data/")
    
    # Filter out already uploaded
    to_upload = [p for p in pdfs if p.name not in existing]
    print(f"📥 {len(to_upload)} new PDFs to upload")
    print()
    
    if not to_upload:
        print("✅ All PDFs already uploaded!")
        return
    
    manifest = dict(existing)
    success = 0
    failed = 0
    
    # Upload one at a time (Vercel Blob has rate limits)
    for i, pdf in enumerate(to_upload, 1):
        size_mb = pdf.stat().st_size / (1024 * 1024)
        print(f"  [{i}/{len(to_upload)}] Uploading {pdf.name} ({size_mb:.1f} MB)...", end="", flush=True)
        
        result = upload_file(pdf)
        if result:
            manifest[pdf.name] = result["url"]
            success += 1
            print(f" ✅")
        else:
            failed += 1
            print()
        
        # Save manifest periodically
        if i % 10 == 0:
            MANIFEST_FILE.write_text(json.dumps(manifest, indent=2))
    
    # Save final manifest
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2))
    
    print()
    print("🎉 Upload complete!")
    print(f"   ✅ Success: {success}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📋 Manifest: {MANIFEST_FILE}")


if __name__ == "__main__":
    main()
