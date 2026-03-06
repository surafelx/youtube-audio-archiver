"""
YouTube Audio Archiver - Web UI + Simple Download Script
A Flask web interface that triggers the simple yt-dlp subprocess.
"""

import os
import sys
import threading
import subprocess
import time
import logging
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response, stream_with_context
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent.resolve()
CHANNELS_FILE = BASE_DIR / "channels.txt"
DOWNLOADS_DIR = BASE_DIR / "downloads"
TEMPLATE_DIR = BASE_DIR / "templates"

# Track log lines for streaming
log_lines = []
log_lines_lock = threading.Lock()

# Download process
download_process = None
download_thread = None

# ============================================================================
# FLASK APPLICATION
# ============================================================================

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))

@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('index.html')

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/status')
def get_status():
    """Get current downloader status."""
    status = 'IDLE'
    if download_process and download_process.poll() is None:
        status = 'RUNNING'
    return jsonify({'status': status})

@app.route('/api/channels', methods=['GET', 'POST', 'DELETE'])
def manage_channels():
    """Manage channel list."""
    if request.method == 'GET':
        channels = load_channels()
        return jsonify({'channels': channels})
    
    elif request.method == 'POST':
        data = request.json
        channel_url = data.get('url', '').strip()
        if channel_url:
            channels = load_channels()
            if channel_url not in channels:
                channels.append(channel_url)
                save_channels(channels)
                log_message(f"Added channel: {channel_url}")
            return jsonify({'success': True, 'channels': channels})
        return jsonify({'success': False, 'error': 'No URL provided'}), 400
    
    elif request.method == 'DELETE':
        data = request.json
        channel_url = data.get('url', '').strip()
        if channel_url:
            channels = load_channels()
            if channel_url in channels:
                channels.remove(channel_url)
                save_channels(channels)
                log_message(f"Removed channel: {channel_url}")
            return jsonify({'success': True, 'channels': channels})
        return jsonify({'success': False, 'error': 'No URL provided'}), 400

@app.route('/api/start', methods=['POST'])
def start_download():
    """Start the simple download script as subprocess."""
    global download_process, download_thread
    
    # Check if already running
    if download_process and download_process.poll() is None:
        return jsonify({'success': False, 'error': 'Download already running'}), 400
    
    data = request.json or {}
    test_mode = data.get('test_mode', False)
    limit = data.get('limit', 0)  # 0 = unlimited
    
    log_message("="*50)
    log_message("Starting download with parameters:")
    log_message(f"  Test mode: {test_mode}")
    log_message(f"  Limit: {limit if limit > 0 else 'All'}")
    log_message("="*50)
    
    # Build command
    cmd = [sys.executable, str(BASE_DIR / 'download_simple.py')]
    
    if test_mode:
        cmd.append('--test')
    if limit > 0:
        cmd.extend(['--limit', str(limit)])
    
    # Start subprocess
    download_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1,
        cwd=str(BASE_DIR)
    )
    
    # Start thread to read output
    download_thread = threading.Thread(target=read_process_output, daemon=True)
    download_thread.start()
    
    return jsonify({'success': True})

@app.route('/api/stop', methods=['POST'])
def stop_download():
    """Stop the running download."""
    global download_process
    
    if download_process and download_process.poll() is None:
        download_process.terminate()
        log_message("Download stopped by user")
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'No download running'}), 400

@app.route('/api/logs')
def get_logs():
    """Get recent log entries."""
    with log_lines_lock:
        return jsonify({'logs': '\n'.join(log_lines[-100:])})

@app.route('/api/logs/stream')
def stream_logs():
    """Stream logs in real-time using Server-Sent Events."""
    def generate():
        last_index = 0
        while True:
            with log_lines_lock:
                if len(log_lines) > last_index:
                    for i in range(last_index, len(log_lines)):
                        yield f"data: {log_lines[i]}\n\n"
                    last_index = len(log_lines)
            time.sleep(0.5)
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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

def save_channels(channels):
    """Save channels to file."""
    with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
        f.write("# YouTube Channel List\n")
        for channel in channels:
            f.write(f"{channel}\n")

def log_message(msg):
    """Add a message to the log."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {msg}"
    with log_lines_lock:
        log_lines.append(log_line)
        if len(log_lines) > 1000:
            log_lines[:] = log_lines[-1000:]

def read_process_output():
    """Read output from the download subprocess."""
    global download_process
    if not download_process:
        return
    
    for line in download_process.stdout:
        line = line.strip()
        if line:
            log_message(line)
    
    # Process finished
    download_process = None
    log_message("="*50)
    log_message("Download process completed")
    log_message("="*50)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    log_message("Server started. Open http://localhost:8000")
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)
