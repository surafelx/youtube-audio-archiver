# YouTube Audio Archiver

A simple, reliable YouTube audio downloader with a web UI. Downloads audio as MP3 from YouTube channels.

## Features

- 🌐 **Web UI** - Easy-to-use interface for managing channels and monitoring downloads
- ⚡ **Simple & Fast** - Uses yt-dlp directly via subprocess (no complex dependencies)
- 📺 **Channel Support** - Download all videos from a YouTube channel
- 🎵 **MP3 Output** - Extracts audio as high-quality MP3 files
- 🔄 **Resume Support** - Tracks downloaded videos to avoid re-downloading
- 📊 **Live Logs** - Real-time progress streaming in the browser
- ⚙️ **Configurable** - Set download limits and test mode

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Add Channels

Edit `channels.txt` and add one YouTube channel URL per line:

```
https://www.youtube.com/@channelname1/videos
https://www.youtube.com/@channelname2/videos
```

Or add them via the web UI.

### 3. Run the Web UI

```bash
python app.py
```

Then open http://localhost:8000 in your browser.

### 4. Start Downloading

- Check "Test Mode" to download only 5 videos per channel (for testing)
- Set "Max Downloads" to limit total videos (0 = unlimited)
- Click "Start Download"

## Usage Options

### Option 1: Web UI (Recommended)

```bash
python app.py
```

Open http://localhost:8000

### Option 2: Command Line

```bash
# Download with test mode (5 videos)
python download_simple.py --test

# Download with limit
python download_simple.py --limit 10

# Both options
python download_simple.py --test --limit 5
```

## Configuration

| File | Description |
|------|-------------|
| `channels.txt` | List of YouTube channel URLs (one per line) |
| `archive.txt` | Tracks downloaded videos (auto-managed) |
| `downloads/` | Where MP3 files are saved |

## Requirements

- Python 3.8+
- yt-dlp
- imageio-ffmpeg (for audio extraction)
- Flask (for web UI)

Install all with:
```bash
pip install -r requirements.txt
```

## Troubleshooting

### "No JavaScript runtime found" error
This is normal - the app uses the Android API client which doesn't require JavaScript.

### Videos not downloading
- Make sure channels.txt has valid YouTube channel URLs
- Check the logs in the web UI for errors
- Try disabling Test Mode to download all videos

### FFmpeg not found
Install ffmpeg or use the included imageio-ffmpeg (auto-installed with requirements.txt)

## How It Works

1. **Web UI** (`app.py`) provides a browser interface
2. When you click "Start", it spawns `download_simple.py` as a subprocess
3. `download_simple.py` uses yt-dlp with the Android API client
4. yt-dlp downloads videos and ffmpeg extracts audio as MP3
5. Downloaded video IDs are saved to `archive.txt` to avoid re-downloading

## License

MIT
