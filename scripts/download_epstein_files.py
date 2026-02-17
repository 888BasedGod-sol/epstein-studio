#!/usr/bin/env python3
"""
Download Epstein Files datasets from public archives and extract PDFs.

Sources:
- Internet Archive mirrors
- copyparty.vvv.systems mirrors
- Official DOJ (fallback)

Reference: https://github.com/yung-megafone/Epstein-Files
"""

import os
import sys
import zipfile
import ipaddress
import socket
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Optional
import hashlib
import time

# Dataset metadata from yung-megafone/Epstein-Files README
DATASETS = {
    1: {
        "size_mb": 1230,
        "urls": [
            "https://archive.org/download/data-set-1/DataSet%201.zip",
            "https://copyparty.vvv.systems/DOJ%20Epstein%20Files/justice.gov/DataSet%201.zip",
            "https://www.justice.gov/epstein/files/DataSet%201.zip",
        ],
        "sha256": "598F4D2D71F0D183CF898CD9D6FB8EC1F6161E0E71D8C37897936AEF75F860B4",
    },
    2: {
        "size_mb": 630,
        "urls": [
            "https://archive.org/download/data-set-1/DataSet%202.zip",
            "https://copyparty.vvv.systems/DOJ%20Epstein%20Files/justice.gov/DataSet%202.zip",
            "https://www.justice.gov/epstein/files/DataSet%202.zip",
        ],
        "sha256": "24CEBBAEFE9D49BCA57726B5A4B531FF20E6A97C370BA87A7593DD8DBDB77BFF",
    },
    3: {
        "size_mb": 595,
        "urls": [
            "https://archive.org/download/data-set-1/DataSet%203.zip",
            "https://copyparty.vvv.systems/DOJ%20Epstein%20Files/justice.gov/DataSet%203.zip",
            "https://www.justice.gov/epstein/files/DataSet%203.zip",
        ],
        "sha256": "160231C8C689C76003976B609E55689530FC4832A1535CE13BFCD8F871C21E65",
    },
    4: {
        "size_mb": 351,
        "urls": [
            "https://archive.org/download/data-set-1/DataSet%204.zip",
            "https://copyparty.vvv.systems/DOJ%20Epstein%20Files/justice.gov/DataSet%204.zip",
            "https://www.justice.gov/epstein/files/DataSet%204.zip",
        ],
        "sha256": "979154842BAC356EF36BB2D0E72F78E0F6B771D79E02DD6934CFF699944E2B71",
    },
    5: {
        "size_mb": 61,
        "urls": [
            "https://archive.org/download/data-set-1/DataSet%205.zip",
            "https://copyparty.vvv.systems/DOJ%20Epstein%20Files/justice.gov/DataSet%205.zip",
            "https://www.justice.gov/epstein/files/DataSet%205.zip",
        ],
        "sha256": "7317E2AD089C82A59378A9C038E964FEAB246BE62ECC24663B741617AF3DA709",
    },
    6: {
        "size_mb": 51,
        "urls": [
            "https://archive.org/download/data-set-1/DataSet%206.zip",
            "https://copyparty.vvv.systems/DOJ%20Epstein%20Files/justice.gov/DataSet%206.zip",
            "https://www.justice.gov/epstein/files/DataSet%206.zip",
        ],
        "sha256": "D54D26D94127B9A277CF3F7D9EEAF9A7271F118757997EDAC3BC6E1039ED6555",
    },
    7: {
        "size_mb": 97,
        "urls": [
            "https://archive.org/download/data-set-1/DataSet%207.zip",
            "https://copyparty.vvv.systems/DOJ%20Epstein%20Files/justice.gov/DataSet%207.zip",
            "https://www.justice.gov/epstein/files/DataSet%207.zip",
        ],
        "sha256": "51E1961B3BCF18A21AFD9BCF697FDB54DAC97D1B64CF88297F4C5BE268D26B8E",
    },
    8: {
        "size_mb": 10670,
        "urls": [
            "https://archive.org/download/data-set-8/DataSet%208.zip",
            "https://copyparty.vvv.systems/DOJ%20Epstein%20Files/justice.gov/DataSet%208.zip",
            "https://www.justice.gov/epstein/files/DataSet%208.zip",
        ],
        "sha256": "8cb7345bf7a0b32f183658ac170fb0b6527895c95f0233d7b99d544579567294",
    },
    # Dataset 9 is incomplete and ~180GB - skip for now
    10: {
        "size_mb": 78650,
        "urls": [
            "https://archive.org/download/data-set-10/DataSet%2010.zip",
            "https://copyparty.vvv.systems/DOJ%20Epstein%20Files/justice.gov/DataSet%2010.zip",
            "https://www.justice.gov/epstein/files/DataSet%2010.zip",
        ],
        "sha256": "7D6935B1C63FF2F6BCABDD024EBC2A770F90C43B0D57B646FA7CBD4C0ABCF846",
    },
    11: {
        "size_mb": 27500,
        "urls": [
            "https://copyparty.vvv.systems/DOJ%20Epstein%20Files/justice.gov/DataSet%2011.zip",
            "https://www.justice.gov/epstein/files/DataSet%2011.zip",
        ],
        "sha256": "9714273B9E325F0A1F406063C795DB32F5DA2095B75E602D4C4FBABA5DE3ED80",
    },
    12: {
        "size_mb": 114,
        "urls": [
            "https://archive.org/download/data-set-12_202601/DataSet%2012.zip",
            "https://copyparty.vvv.systems/DOJ%20Epstein%20Files/justice.gov/DataSet%2012.zip",
            "https://www.justice.gov/epstein/files/DataSet%2012.zip",
        ],
        "sha256": "B5314B7EFCA98E25D8B35E4B7FAC3EBB3CA2E6CFD0937AA2300CA8B71543BBE2",
    },
}

# Where to store downloads and extracted PDFs
DOWNLOAD_DIR = Path(__file__).parent.parent / "downloads"
DATA_DIR = Path(__file__).parent.parent / "data"
ALLOWED_DOWNLOAD_HOSTS = {"archive.org", "copyparty.vvv.systems", "www.justice.gov"}


def is_allowed_download_url(url: str) -> bool:
    """Allow only HTTPS downloads from approved mirror hosts."""
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return False

    if parsed.scheme != "https" or not parsed.hostname:
        return False

    hostname = parsed.hostname.lower()
    if hostname not in ALLOWED_DOWNLOAD_HOSTS:
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


def download_file(url: str, dest: Path, expected_size_mb: int = 0) -> bool:
    """Download a file with progress reporting and resumption support."""
    print(f"  📥 Downloading from: {url}")
    if not is_allowed_download_url(url):
        print(f"     ❌ Blocked non-allowlisted URL: {url}")
        return False
    
    # Check if partial download exists
    existing_size = dest.stat().st_size if dest.exists() else 0
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    
    # Try to resume if partial
    if existing_size > 0:
        headers["Range"] = f"bytes={existing_size}-"
        print(f"     Resuming from {existing_size / 1024 / 1024:.1f} MB")
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            # Check if server supports resumption
            if existing_size > 0 and resp.status != 206:
                print("     Server doesn't support resumption, starting fresh")
                existing_size = 0
            
            total_size = int(resp.headers.get("Content-Length", 0))
            if resp.status == 206:
                # Partial content - add existing size
                total_size += existing_size
            
            # Open file in append or write mode
            mode = "ab" if existing_size > 0 and resp.status == 206 else "wb"
            
            downloaded = existing_size
            chunk_size = 1024 * 1024  # 1MB chunks
            last_report = time.time()
            
            with open(dest, mode) as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Report progress every 5 seconds
                    now = time.time()
                    if now - last_report > 5:
                        pct = (downloaded / total_size * 100) if total_size else 0
                        print(f"     Progress: {downloaded / 1024 / 1024:.1f} MB ({pct:.1f}%)")
                        last_report = now
            
            print(f"     ✅ Downloaded {downloaded / 1024 / 1024:.1f} MB")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"     ❌ HTTP error: {e.code} {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"     ❌ URL error: {e.reason}")
        return False
    except OSError as e:
        print(f"     ❌ Error: {e}")
        return False


def verify_hash(file_path: Path, expected_hash: str) -> bool:
    """Verify SHA256 hash of a file."""
    print(f"  🔍 Verifying SHA256...")
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    actual = sha256.hexdigest().upper()
    expected = expected_hash.upper()
    if actual == expected:
        print(f"     ✅ Hash verified")
        return True
    else:
        print(f"     ❌ Hash mismatch!")
        print(f"        Expected: {expected}")
        print(f"        Got:      {actual}")
        return False


def extract_pdfs(zip_path: Path, dest_dir: Path, dataset_num: int) -> int:
    """Extract all PDFs from a zip file to the destination directory."""
    print(f"  📦 Extracting PDFs from {zip_path.name}...")
    
    count = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            if member.lower().endswith(".pdf"):
                # Extract just the filename, not the full path
                filename = Path(member).name
                if not filename:
                    continue
                
                # Add dataset prefix to avoid collisions
                # dest_filename = f"ds{dataset_num:02d}_{filename}"
                dest_filename = filename  # Keep original name
                dest_path = dest_dir / dest_filename
                
                if dest_path.exists():
                    continue  # Skip existing
                
                try:
                    # Read from zip and write to destination
                    with zf.open(member) as src:
                        dest_path.write_bytes(src.read())
                    count += 1
                except Exception as e:
                    print(f"     ⚠️ Failed to extract {filename}: {e}")
    
    print(f"     ✅ Extracted {count} PDFs")
    return count


def download_dataset(dataset_num: int, skip_verify: bool = False) -> int:
    """Download and extract a single dataset. Returns number of PDFs extracted."""
    if dataset_num not in DATASETS:
        print(f"❌ Dataset {dataset_num} not configured")
        return 0
    
    info = DATASETS[dataset_num]
    zip_filename = f"DataSet_{dataset_num}.zip"
    zip_path = DOWNLOAD_DIR / zip_filename
    
    print(f"\n{'='*60}")
    print(f"📁 Dataset {dataset_num} ({info['size_mb']} MB)")
    print(f"{'='*60}")
    
    # Create directories
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    
    # Check if already downloaded and verified
    if zip_path.exists():
        expected_size = info["size_mb"] * 1024 * 1024 * 0.9  # Allow 10% variance
        actual_size = zip_path.stat().st_size
        if actual_size >= expected_size:
            print(f"  📋 Found existing download: {actual_size / 1024 / 1024:.1f} MB")
            if not skip_verify:
                if not verify_hash(zip_path, info["sha256"]):
                    print("  🔄 Re-downloading due to hash mismatch...")
                    zip_path.unlink()
    
    # Download if needed
    if not zip_path.exists() or zip_path.stat().st_size < 1000:
        success = False
        for url in info["urls"]:
            if download_file(url, zip_path, info["size_mb"]):
                success = True
                break
            print("     Trying next mirror...")
        
        if not success:
            print(f"  ❌ Failed to download dataset {dataset_num} from any source")
            return 0
        
        # Verify after download
        if not skip_verify and not verify_hash(zip_path, info["sha256"]):
            print("  ⚠️ Hash verification failed, file may be corrupted")
    
    # Extract PDFs
    try:
        count = extract_pdfs(zip_path, DATA_DIR, dataset_num)
        return count
    except zipfile.BadZipFile as e:
        print(f"  ❌ Bad zip file: {e}")
        return 0


def main():
    print("=" * 60)
    print("🗂️  Epstein Files Downloader")
    print("=" * 60)
    print()
    print("Source: https://github.com/yung-megafone/Epstein-Files")
    print("These are publicly released DOJ court documents.")
    print()
    print("Available datasets:")
    print("  Small (< 1 GB):  1-7, 12")
    print("  Medium (10 GB):  8")
    print("  Large (27-78 GB): 10, 11")
    print("  Skipped:         9 (incomplete, ~180 GB)")
    print()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            datasets_to_download = [1, 2, 3, 4, 5, 6, 7, 12]  # Start with small ones
        elif sys.argv[1] == "--all-large":
            datasets_to_download = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12]
        else:
            try:
                datasets_to_download = [int(x) for x in sys.argv[1:]]
            except ValueError:
                print("Usage: python download_epstein_files.py [dataset_numbers...] | --all | --all-large")
                print("  Examples:")
                print("    python download_epstein_files.py 1 2 3      # Download datasets 1, 2, 3")
                print("    python download_epstein_files.py --all     # Download all small datasets (1-7, 12)")
                print("    python download_epstein_files.py --all-large  # Download everything except DS9")
                sys.exit(1)
    else:
        # Default: download small datasets only
        print("No datasets specified. Downloading small datasets (1-7, 12)...")
        print("Use --all-large for everything (but it's 120+ GB)")
        print()
        datasets_to_download = [1, 2, 3, 4, 5, 6, 7, 12]
    
    total_pdfs = 0
    for ds_num in datasets_to_download:
        count = download_dataset(ds_num)
        total_pdfs += count
    
    print()
    print("=" * 60)
    print(f"✅ Done! Extracted {total_pdfs} total PDFs to {DATA_DIR}")
    print()
    print("Next steps:")
    print("  1. Run: python scripts/upload_to_blob.py")
    print("     (uploads PDFs to Vercel Blob storage)")
    print()
    print("  2. Deploy: vercel --prod")
    print()


if __name__ == "__main__":
    main()
