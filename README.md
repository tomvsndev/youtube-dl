# YouTube Media Downloader

A comprehensive Python-based YouTube downloader that supports both video and audio formats with various output options.

## Features

- 📥 Download YouTube videos in various formats and resolutions
- 🎵 Extract audio only (MP3, WAV formats)
- 📚 Batch download from a list of URLs
- 🎯 Format selection menu with available options
- 📊 Download progress with speed and ETA indicators
- 🔒 Safe filename handling

## Installation

1. Clone or download this repository
2. Install required dependencies:
   ```bash
   venv -m youtube-dl
   pip install -r requirements.txt
   or (recommended)
   make sure uv is installed:
   uv venv
   uv add -r requirements.txt 
   
   Install FFmpeg:

    Windows:
        Download from https://ffmpeg.org/download.html

        Extract and add the bin folder to your system PATH

    macOS:
    bash

brew install ffmpeg

Ubuntu/Debian:
bash

    sudo apt update
    sudo apt install ffmpeg

Usage

Run the script:
bash

python youtube_downloader.py

Then follow the menu options:

    Download single video/audio - Choose from available formats

    Batch download from file - Provide a text file with URLs (one per line)

    Download best video quality - Automatically selects the highest quality

    Download audio only - Extracts audio as MP3

Supported Formats

    Video: MP4, WebM, FLV, and more

    Audio: MP3, WAV, AAC, and more

    Various resolutions from 144p to 4K (when available)

 

Disclaimer

This tool is for personal use only. Please respect copyright laws and YouTube's Terms of Service. Downloading copyrighted content without permission may violate laws in your country.
License MIT.

This project is for educational purposes. Use responsibly.
