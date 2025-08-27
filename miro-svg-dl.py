#!/usr/bin/env python3
"""
miro_svg_dl.py – bulk-download every SVG stored on a Miro board.

Usage:
    python miro_svg_dl.py -b <BOARD_ID> -t <ACCESS_TOKEN>
Options:
    -o, --out DIR         Destination folder (default: ./svgs)
    --include-docs        Also scan “document” items (files) in addition to
                          “image” items.  Useful if the SVGs were uploaded
                          via the “Upload file” dialog instead of drag-drop.
    --quiet               Suppress per-file log lines.
Notes:
  • The script obeys Miro’s public rate-limit (≤ 4 requests/sec).
  • `BOARD_ID` is the short alphanumeric ID you see in the board URL.
  • `ACCESS_TOKEN` can be a personal access token or an OAuth token with
    at least `boards:read` scope.
"""

import argparse, time, pathlib, sys, requests, urllib.parse, re

API_ROOT = "https://api.miro.com/v2"

def get_items(board_id: str, token: str, item_type: str):
    """
    Generator that yields every item of `item_type` on the board,
    transparently handling pagination.
    """
    url = f"{API_ROOT}/boards/{board_id}/items?type={item_type}&limit=50"
    headers = {"Authorization": f"Bearer {token}"}
    session = requests.Session()
    session.headers.update(headers)

    while url:
        resp = session.get(url, timeout=20)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Error {resp.status_code} when fetching {url}: {resp.text}"
            )
        data = resp.json()
        yield from data.get("data", [])
        cursor = data.get("cursor")
        url = (
            f"{API_ROOT}/boards/{board_id}/items?cursor={cursor}"
            if cursor else None
        )
        time.sleep(0.25)           # ≤ 4 requests per second

def download(url: str, dest: pathlib.Path, session: requests.Session):
    """
    Download `url` (a pre-signed, short-lived Miro link) to `dest`.
    """
    r = session.get(url, allow_redirects=True, timeout=20)
    r.raise_for_status()
    dest.write_bytes(r.content)

def get_filename_from_headers(url: str, session: requests.Session):
    """
    Make a HEAD request to get the filename from Content-Disposition header.
    """
    try:
        r = session.head(url, allow_redirects=True, timeout=10)
        if r.status_code == 200:
            content_disposition = r.headers.get('content-disposition', '')
            if content_disposition:
                # Parse filename from Content-Disposition header
                filename_match = re.search(r'filename="([^"]+)"', content_disposition)
                if filename_match:
                    return filename_match.group(1)
                # Fallback to filename without quotes
                filename_match = re.search(r'filename=([^;]+)', content_disposition)
                if filename_match:
                    return filename_match.group(1).strip()
    except:
        pass
    return None

def main():
    p = argparse.ArgumentParser(
        description="Download all SVGs from a Miro board."
    )
    p.add_argument("-b", "--board", required=True, help="Board ID")
    p.add_argument("-t", "--token", required=True, help="Access token")
    p.add_argument("-o", "--out", default="svgs", help="Output directory")
    p.add_argument("--include-docs", action="store_true",
                   help="Also scan document items")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    out_dir = pathlib.Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {args.token}"})

    # Try all possible item types that might contain SVGs
    scanned_types = ["image", "document", "shape", "sticky_note", "text", "frame", "app_card"]
    total_saved = 0
    files_with_original_names = 0
    files_with_generated_names = 0

    for item_type in scanned_types:
        print(f"Scanning {item_type} items...")
        item_count = 0
        for item in get_items(args.board, args.token, item_type):
            item_count += 1
            # Look for URL in the correct field
            src = item.get("data", {}).get("imageUrl", "")
            item_id = item.get("id", "unknown")
            
            if not args.quiet:
                print(f"  Found {item_type} item {item_id}: {src}")
            
            # Try different approaches to get the actual SVG file
            download_urls_to_try = []
            
            if src:
                # Try the original URL with different format parameters
                base_url = src.split('?')[0]  # Remove all query parameters
                download_urls_to_try = [
                    f"{base_url}?format=original&redirect=true",
                    f"{base_url}?redirect=true", 
                    f"{base_url}?format=original",
                    base_url,  # No parameters
                    src,  # Original URL
                ]
            
            # Test each URL to find one that gives us SVG content
            successful_url = None
            for test_url in download_urls_to_try:
                try:
                    if not args.quiet:
                        print(f"    Trying: {test_url}")
                    
                    # Add rate limiting to avoid hitting API limits
                    time.sleep(0.3)
                    
                    headers = {"Authorization": f"Bearer {args.token}"}
                    test_resp = session.get(test_url, headers=headers, timeout=10, allow_redirects=True)
                    content_type = test_resp.headers.get('content-type', '').lower()
                    
                    if not args.quiet:
                        print(f"      Status: {test_resp.status_code}, Content-Type: {content_type}")
                    
                    # Check if this looks like SVG content
                    is_svg_content = (
                        'svg' in content_type or 
                        test_resp.text.strip().startswith('<?xml') and 'svg' in test_resp.text[:200] or
                        test_resp.text.strip().startswith('<svg') or
                        'image/svg' in content_type
                    )
                    
                    if test_resp.status_code == 200 and is_svg_content:
                        successful_url = test_url
                        if not args.quiet:
                            print(f"      ✓ Found SVG content!")
                        break
                    elif test_resp.status_code == 200 and not args.quiet:
                        # Show first 100 chars of content to debug
                        preview = test_resp.text[:100].replace('\n', ' ')
                        print(f"      Content preview: {preview}...")
                        
                except Exception as e:
                    if not args.quiet:
                        print(f"      ⚠️  Error: {e}")
                    continue
            
            if not successful_url:
                if not args.quiet:
                    print(f"    ✗ No SVG content found for this item")
                continue
            
            src = successful_url
            
            # Get original filename from HTTP headers
            original_filename = get_filename_from_headers(src, session)
            if original_filename and not args.quiet:
                print(f"    Original filename: {original_filename}")
            
            # Generate filename - prefer original name, fallback to item ID
            if original_filename:
                # Sanitize filename for filesystem compatibility
                safe_filename = re.sub(r'[<>:"/\\|?*]', '_', original_filename)
                safe_filename = safe_filename.strip('. ')  # Remove leading/trailing dots and spaces
                
                # Ensure it ends with .svg
                if not safe_filename.lower().endswith('.svg'):
                    safe_filename += '.svg'
                    
                filename = safe_filename
            else:
                # Fallback to item ID
                filename = f"{item['id']}.svg"
                if not args.quiet:
                    print(f"    No original filename found, using item ID")
            
            dest = out_dir / filename
            
            # Handle filename conflicts by adding a counter
            original_dest = dest
            counter = 1
            while dest.exists():
                if original_filename:
                    name_part = safe_filename.rsplit('.svg', 1)[0]
                    filename = f"{name_part}_{counter}.svg"
                else:
                    filename = f"{item['id']}_{counter}.svg"
                dest = out_dir / filename
                counter += 1
                
            if not args.quiet and dest != original_dest:
                print(f"    Filename conflict resolved: {filename}")
            try:
                download(src, dest, session)
                total_saved += 1
                
                # Track filename type for summary
                if original_filename:
                    files_with_original_names += 1
                else:
                    files_with_generated_names += 1
                    
                if not args.quiet:
                    print("✓", dest)
            except Exception as e:
                print("⚠️  Failed to download", src, "→", e, file=sys.stderr)
        print(f"  Total {item_type} items found: {item_count}")

    print(f"\nDone. Saved {total_saved} SVG file(s) to {out_dir}")
    if total_saved > 0:
        print(f"  • {files_with_original_names} files kept their original names")
        print(f"  • {files_with_generated_names} files used generated names (item IDs)")

if __name__ == "__main__":
    main()