"""
Video Links Downloader using yt-dlp.
Reads individual video links from video_links.txt and downloads audio as MP3.
Tracks download status in video_archive.txt.
"""

import subprocess
import sys
import argparse
import time
import random
from pathlib import Path
import imageio_ffmpeg
import re
from datetime import datetime

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
VIDEO_LINKS_FILE = BASE_DIR / "video_links.txt"
VIDEO_ARCHIVE_FILE = BASE_DIR / "video_archive.txt"
DOWNLOADS_DIR = BASE_DIR / "downloads" / "videos"

# Get ffmpeg path
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

def ensure_directories():
    """Ensure required directories exist."""
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

def load_video_links():
    """Load video links from file."""
    links = []
    if VIDEO_LINKS_FILE.exists():
        with open(VIDEO_LINKS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    links.append(line)
    return links

def load_archive():
    """Load already downloaded video IDs from archive."""
    downloaded = {}
    if VIDEO_ARCHIVE_FILE.exists():
        with open(VIDEO_ARCHIVE_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Format: video_id | status | timestamp | title
                    parts = line.split('|')
                    if len(parts) >= 2:
                        video_id = parts[0].strip()
                        status = parts[1].strip()
                        title = parts[2].strip() if len(parts) > 2 else "Unknown"
                        downloaded[video_id] = {'status': status, 'title': title}
    return downloaded

def save_to_archive(video_id, status, title):
    """Save download status to archive file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(VIDEO_ARCHIVE_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{video_id} | {status} | {title} | {timestamp}\n")

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats."""
    # youtube.com/watch?v=VIDEO_ID
    match = re.search(r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    if match:
        return match.group(1)
    return None

def get_video_info(video_url):
    """Get video information (title, duration, etc.) using yt-dlp."""
    cmd = [
        sys.executable, '-m', 'yt_dlp',
        '--flat-playlist',
        '--print', '%(id)s|%(title)s|%(duration)s',
    ]
    cmd.append(video_url)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=60
        )
        output = result.stdout.strip()
        if output:
            parts = output.split('|')
            if len(parts) >= 2:
                return {
                    'id': parts[0].strip(),
                    'title': parts[1].strip(),
                    'duration': parts[2].strip() if len(parts) > 2 else "0"
                }
    except Exception as e:
        print(f"Error getting video info: {e}")
    
    # Fallback: extract ID and use URL as title
    video_id = extract_video_id(video_url)
    return {
        'id': video_id or "unknown",
        'title': f"Video_{video_id}" if video_id else "Unknown",
        'duration': "0"
    }

def download_video(video_url, test_mode=False, min_duration=0):
    """Download a single video and convert to MP3."""
    
    # Get video info first
    print(f"Getting video information...")
    video_info = get_video_info(video_url)
    video_id = video_info['id']
    video_title = video_info['title']
    
    print(f"Video ID: {video_id}")
    print(f"Title: {video_title}")
    
    # Check minimum duration
    if min_duration > 0:
        try:
            duration = int(video_info['duration']) if video_info['duration'] else 0
            if duration > 0 and duration < min_duration:
                print(f"[SKIP] Video duration ({duration}s) is less than minimum ({min_duration}s)")
                return {'success': False, 'skipped': True, 'reason': 'duration'}
        except:
            pass
    
    # Build yt-dlp command
    cmd = [
        sys.executable, '-m', 'yt_dlp',
        '--ffmpeg-location', FFMPEG_PATH,
        '--extract-audio',
        '--audio-format', 'mp3',
        '--audio-quality', '0',
        '--output', str(DOWNLOADS_DIR / '%(title)s.%(ext)s'),
        # Retry settings
        '--retries', '10',
        '--extractor-retries', '5',
        # Sleep between videos to avoid throttling
        '--sleep-interval', '2',
        '--max-sleep-interval', '5',
        # Progress bar
        '--progress',
    ]
    
    if test_mode:
        print("[TEST MODE] Would download this video")
        return {'success': True, 'test': True}
    
    cmd.append(video_url)
    
    print(f"\n{'='*60}")
    print(f"Downloading: {video_title}")
    print(f"{'='*60}\n")
    
    try:
        # Run yt-dlp, capturing output for real-time logging
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1
        )
        
        # Read and print output line by line
        for line in process.stdout:
            print(line.strip())
        
        process.wait()
        
        if process.returncode == 0:
            # Save to archive on success
            save_to_archive(video_id, "done", video_title)
            return {'success': True, 'video_id': video_id, 'title': video_title}
        else:
            save_to_archive(video_id, "failed", video_title)
            return {'success': False, 'video_id': video_id, 'title': video_title}
            
    except Exception as e:
        print(f"Error: {e}")
        save_to_archive(video_id, "error", video_title)
        return {'success': False, 'error': str(e)}

def show_status():
    """Show download status for all videos."""
    print("\n" + "=" * 60)
    print("VIDEO DOWNLOAD STATUS")
    print("=" * 60)
    
    # Load all links
    links = load_video_links()
    archive = load_archive()
    
    if not links:
        print("No video links found in video_links.txt")
        return
    
    print(f"\nTotal videos in list: {len(links)}")
    
    done_count = 0
    pending_count = 0
    failed_count = 0
    
    print("\n--- DOWNLOADED (done) ---")
    for link in links:
        video_id = extract_video_id(link)
        if video_id and video_id in archive:
            if archive[video_id]['status'] == 'done':
                done_count += 1
                print(f"  [DONE] {archive[video_id]['title']}")
    
    print("\n--- PENDING ---")
    for link in links:
        video_id = extract_video_id(link)
        if not video_id:
            pending_count += 1
            print(f"  [PENDING] {link}")
        elif video_id not in archive:
            pending_count += 1
            info = get_video_info(link)
            print(f"  [PENDING] {info['title']}")
        elif archive[video_id]['status'] == 'failed':
            failed_count += 1
            print(f"  [FAILED] {archive[video_id]['title']} - run again to retry")
    
    print("\n" + "-" * 40)
    print(f"Done: {done_count}")
    print(f"Pending: {pending_count}")
    print(f"Failed: {failed_count}")
    print(f"Progress: {done_count}/{len(links)} ({100*done_count//len(links)}%)")
    print("=" * 60 + "\n")

def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='YouTube Video Links Downloader')
    parser.add_argument('--test', action='store_true', help='Test mode - show what would be downloaded')
    parser.add_argument('--status', action='store_true', help='Show download status only')
    parser.add_argument('--min-duration', type=int, default=0, help='Minimum video duration in seconds (0=download all)')
    parser.add_argument('--force', action='store_true', help='Force re-download of already downloaded videos')
    parser.add_argument('--retry-failed', action='store_true', help='Retry downloading failed videos')
    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_directories()
    
    print("YouTube Video Links Downloader")
    print("=" * 40)
    print(f"Links file: {VIDEO_LINKS_FILE}")
    print(f"Archive file: {VIDEO_ARCHIVE_FILE}")
    print(f"Downloads dir: {DOWNLOADS_DIR}")
    
    # Show status if requested
    if args.status:
        show_status()
        return
    
    # Load video links
    links = load_video_links()
    
    if not links:
        print("\nNo video links found in video_links.txt")
        print("Add video URLs (one per line) to video_links.txt")
        return
    
    print(f"\nFound {len(links)} video link(s)")
    
    # Load archive
    archive = load_archive()
    
    # Filter links to download
    links_to_download = []
    for link in links:
        video_id = extract_video_id(link)
        
        if args.retry_failed:
            # Include failed videos for retry
            if video_id and video_id in archive:
                if archive[video_id]['status'] == 'failed':
                    links_to_download.append(link)
            elif not video_id or video_id not in archive:
                links_to_download.append(link)
        elif args.force:
            # Include all videos
            links_to_download.append(link)
        else:
            # Only include not-yet-downloaded videos
            if not video_id or video_id not in archive:
                links_to_download.append(link)
            elif archive.get(video_id, {}).get('status') != 'done':
                links_to_download.append(link)
    
    if not links_to_download:
        print("\nAll videos already downloaded! Use --force to re-download or --status to see details.")
        show_status()
        return
    
    print(f"Videos to download: {len(links_to_download)}")
    if args.min_duration > 0:
        print(f"Minimum video duration: {args.min_duration} seconds")
    if args.test:
        print("TEST MODE: No actual downloads")
    print()
    
    # Download each video
    success_count = 0
    skip_count = 0
    
    for i, link in enumerate(links_to_download, 1):
        print(f"\n[{i}/{len(links_to_download)}] Processing: {link}")
        
        result = download_video(link, test_mode=args.test, min_duration=args.min_duration)
        
        if result.get('test'):
            print(f"[TEST] Would download: {link}")
            success_count += 1
        elif result.get('skipped'):
            print(f"[SKIP] Video skipped: {result.get('reason', 'unknown')}")
            skip_count += 1
        elif result.get('success'):
            print(f"[OK] Downloaded: {result.get('title', link)}")
            success_count += 1
        else:
            print(f"[FAIL] Failed to download: {link}")
        
        # Sleep between videos to avoid throttling
        if i < len(links_to_download):
            sleep_time = random.randint(3, 8)
            print(f"[WAIT] Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
    
    print("\n" + "=" * 40)
    print(f"Download complete!")
    print(f"Success: {success_count}, Skipped: {skip_count}")
    print(f"Files saved to: {DOWNLOADS_DIR}")
    print("=" * 40)
    
    # Show final status
    show_status()

if __name__ == '__main__':
    main()
