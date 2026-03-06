"""
Simple YouTube Audio Downloader using yt-dlp directly.
Reads channels from channels.txt and downloads audio.
"""

import subprocess
import sys
import argparse
from pathlib import Path
import imageio_ffmpeg

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
CHANNELS_FILE = BASE_DIR / "channels.txt"
DOWNLOADS_DIR = BASE_DIR / "downloads"
ARCHIVE_FILE = BASE_DIR / "archive.txt"

# Get ffmpeg path
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

def load_channels():
    """Load channels from file."""
    channels = []
    if CHANNELS_FILE.exists():
        with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    channels.append(line)
    return channels

def download_with_ytdlp(channel_url, test_mode=False, limit=0):
    """Download audio from a channel using yt-dlp CLI."""
    
    # Build yt-dlp command - using CLI directly
    cmd = [
        sys.executable, '-m', 'yt_dlp',
        '--ffmpeg-location', FFMPEG_PATH,
        '--extract-audio',
        '--audio-format', 'mp3',
        '--audio-quality', '0',
        '--output', str(DOWNLOADS_DIR / '%(uploader)s' / '%(title)s.%(ext)s'),
        '--download-archive', str(ARCHIVE_FILE),
        # Use android client to avoid cookie/browser issues
        '--extractor-args', 'youtube:player_client=android',
        # Retry settings
        '--retries', '10',
        '--extractor-retries', '5',
        # Sleep to avoid throttling
        '--sleep-interval', '3',
        '--max-sleep-interval', '7',
        # Only download videos longer than 2 minutes
        '--match-filter', 'duration > 120',
        # Continue on errors
        '--ignore-errors',
        '--verbose',
    ]
    
    # Add test mode (limit to 5 videos)
    if test_mode:
        cmd.extend(['--playlist-end', '5'])
        print("[TEST MODE] Limiting to 5 videos per channel")
    
    # Add limit if specified
    if limit > 0:
        cmd.extend(['--max-downloads', str(limit)])
        print(f"[LIMIT] Limiting to {limit} downloads")
    
    cmd.append(channel_url)
    
    print(f"\n{'='*60}")
    print(f"Downloading from: {channel_url}")
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
        return process.returncode == 0
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='YouTube Audio Downloader')
    parser.add_argument('--test', action='store_true', help='Test mode - download only 5 videos per channel')
    parser.add_argument('--limit', type=int, default=0, help='Maximum number of videos to download (0=unlimited)')
    args = parser.parse_args()
    
    print("YouTube Audio Downloader (yt-dlp direct)")
    print("=" * 40)
    
    # Load channels
    channels = load_channels()
    
    if not channels:
        print("No channels found in channels.txt")
        print("Add channel URLs (one per line) to channels.txt")
        return
    
    print(f"Found {len(channels)} channel(s) to process")
    print(f"Downloads will be saved to: {DOWNLOADS_DIR}")
    print(f"Archive file: {ARCHIVE_FILE}")
    if args.test:
        print("TEST MODE: Only 5 videos per channel")
    if args.limit > 0:
        print(f"LIMIT: Max {args.limit} downloads")
    print()
    
    # Download from each channel
    for i, channel in enumerate(channels, 1):
        print(f"\n[{i}/{len(channels)}] Processing channel...")
        success = download_with_ytdlp(channel, test_mode=args.test, limit=args.limit)
        if success:
            print(f"[OK] Channel processed")
        else:
            print(f"[FAIL] Channel had errors (continuing to next)")
    
    print("\n" + "=" * 40)
    print("All downloads complete!")
    print(f"Files saved to: {DOWNLOADS_DIR}")

if __name__ == '__main__':
    main()
