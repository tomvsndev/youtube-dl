import yt_dlp
import os
import re
import shutil
import json
from pathvalidate import sanitize_filename


def check_ffmpeg_installed():
    """Check if ffmpeg and ffprobe are available and return their paths"""
    ffmpeg_path = shutil.which('ffmpeg')
    ffprobe_path = shutil.which('ffprobe')

    if not ffmpeg_path or not ffprobe_path:
        print("❌ ffmpeg/ffprobe not found in PATH")
        print("Please install ffmpeg with: sudo apt install ffmpeg (Linux) or download from https://ffmpeg.org/")
        return None, None

    print(f"✅ ffmpeg found at: {ffmpeg_path}")
    print(f"✅ ffprobe found at: {ffprobe_path}")
    return ffmpeg_path, ffprobe_path


def get_available_formats(url):
    """Get available formats for a YouTube video"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            return formats, info
    except Exception as e:
        print(f"❌ Error getting formats: {e}")
        return None, None


def format_selection_menu(formats, info):
    """Display a menu for format selection"""
    print(f"\n📺 Video: {info.get('title', 'Unknown')}")
    print(f"⏱️  Duration: {info.get('duration', 0)} seconds")
    print(f"👤 Channel: {info.get('uploader', 'Unknown')}")
    print("\nAvailable formats:")

    # Group formats by resolution/quality
    video_formats = {}
    audio_formats = {}

    for f in formats:
        if f.get('vcodec') != 'none' and f.get('acodec') != 'none':  # Video with audio
            resolution = f.get('resolution', 'unknown')
            ext = f.get('ext', 'unknown')
            key = f"{resolution}_{ext}"
            if key not in video_formats:
                video_formats[key] = f
        elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':  # Audio only
            abr = f.get('abr', 0)
            ext = f.get('ext', 'unknown')
            key = f"{abr}kbps_{ext}"
            if key not in audio_formats:
                audio_formats[key] = f

    print("\n🎥 Video formats:")
    video_options = []
    for i, (key, fmt) in enumerate(video_formats.items(), 1):
        print(f"{i}. {key} ({fmt.get('ext')})")
        video_options.append(fmt)

    print("\n🎵 Audio formats:")
    audio_options = []
    for i, (key, fmt) in enumerate(audio_formats.items(), 1):
        j = i + len(video_options)
        print(f"{j}. {key} ({fmt.get('ext')})")
        audio_options.append(fmt)

    total_options = len(video_options) + len(audio_options)

    while True:
        try:
            choice = input(f"\nSelect format (1-{total_options}, or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                return None

            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(video_options):
                return video_options[choice_idx]
            elif len(video_options) <= choice_idx < total_options:
                return audio_options[choice_idx - len(video_options)]
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Please enter a valid number")


def download_youtube_media():
    """
    Download YouTube media with format selection and various output options
    """
    # Check if ffmpeg is installed first
    ffmpeg_path, ffprobe_path = check_ffmpeg_installed()
    if not ffmpeg_path or not ffprobe_path:
        return None

    print("🎬 YouTube Media Downloader 🎬")
    print("-" * 40)

    # Get URL from user
    while True:
        url = input("\n📥 Enter YouTube URL: ").strip()

        if not url:
            print("❌ Please enter a URL")
            continue

        # Basic YouTube URL validation
        youtube_pattern = r'(https?://)?(www\.)?(youtube|youtu)\.(com|be)/.+'
        if not re.match(youtube_pattern, url):
            print("❌ Please enter a valid YouTube URL")
            continue

        break

    # Get available formats
    formats, info = get_available_formats(url)
    if not formats:
        print("❌ Could not retrieve available formats")
        return None

    # Let user select format
    selected_format = format_selection_menu(formats, info)
    if not selected_format:
        return None

    # Get output directory
    output_dir = input("📁 Enter output directory (press Enter for 'downloads'): ").strip()
    output_dir = output_dir if output_dir else "downloads"

    # Get filename
    default_filename = sanitize_filename(info.get('title', 'video'))
    filename = input(f"💾 Enter filename (without extension, press Enter for '{default_filename}'): ").strip()
    filename = filename if filename else default_filename

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get the directory containing ffmpeg
    ffmpeg_dir = os.path.dirname(ffmpeg_path)

    # Set download options based on selection
    format_id = selected_format.get('format_id')
    ext = selected_format.get('ext')

    ydl_opts = {
        'format': format_id,
        'outtmpl': os.path.join(output_dir, f"{filename}.%(ext)s"),
        'ffmpeg_location': ffmpeg_dir,
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [lambda d: print_progress(d)],
    }

    # If it's an audio format, add postprocessing options
    if selected_format.get('vcodec') == 'none':
        # Ask for audio format preference
        print("\n🎵 Audio format options:")
        print("1. MP3 (most compatible)")
        print("2. WAV (lossless, large file)")
        print("3. Keep original format")

        audio_choice = input("Select audio format (1-3, press Enter for MP3): ").strip()
        if audio_choice == "2":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }]
            ext = 'wav'
        elif audio_choice == "3":
            # Keep original format
            pass
        else:  # Default to MP3
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            ext = 'mp3'

    def print_progress(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            print(f"⬇️  Downloading: {percent} complete | Speed: {speed} | ETA: {eta}", end='\r')
        elif d['status'] == 'finished':
            print("\n✅ Download completed!")

    try:
        print(f"\n🚀 Starting download ({selected_format.get('resolution', 'audio')})...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # Get the actual filename that was saved
            final_filename = os.path.splitext(ydl.prepare_filename(info))[0] + f'.{ext}'

            print(f"\n🎉 Successfully downloaded: {info.get('title', 'Unknown title')}")
            print(f"📁 Saved as: {final_filename}")
            print(f"💾 Size: {os.path.getsize(final_filename) / (1024 * 1024):.2f} MB")

            return final_filename

    except Exception as e:
        print(f"\n❌ Error downloading media: {e}")
        return None


def batch_download():
    """Download multiple videos from a text file"""
    ffmpeg_path, ffprobe_path = check_ffmpeg_installed()
    if not ffmpeg_path or not ffprobe_path:
        return None

    print("📚 Batch YouTube Downloader 📚")
    print("-" * 40)

    # Get input file path
    input_file = input("📄 Enter path to text file with URLs (one per line): ").strip()
    if not input_file or not os.path.exists(input_file):
        print("❌ File not found")
        return None

    # Get output directory
    output_dir = input("📁 Enter output directory (press Enter for 'downloads'): ").strip()
    output_dir = output_dir if output_dir else "downloads"
    os.makedirs(output_dir, exist_ok=True)

    # Read URLs from file
    with open(input_file, 'r') as f:
        urls = [line.strip() for line in f.readlines() if line.strip()]

    print(f"📋 Found {len(urls)} URLs to download")

    # Get format preference
    print("\n📹 Select download format:")
    print("1. Best video with audio")
    print("2. Best audio only (MP3)")
    print("3. Best audio only (WAV)")
    print("4. Custom format (will prompt for each video)")

    format_choice = input("Enter choice (1-4, press Enter for best video): ").strip()

    successful_downloads = []

    for i, url in enumerate(urls, 1):
        print(f"\n🔽 Downloading {i}/{len(urls)}: {url}")

        if format_choice == "2":
            # Audio only MP3
            result = download_audio_only(url, output_dir, 'mp3')
        elif format_choice == "3":
            # Audio only WAV
            result = download_audio_only(url, output_dir, 'wav')
        elif format_choice == "4":
            # Custom format for each
            result = download_youtube_media_url(url, output_dir)
        else:
            # Best video
            result = download_best_video(url, output_dir)

        if result:
            successful_downloads.append(result)

    print(f"\n✅ Batch download completed: {len(successful_downloads)}/{len(urls)} successful")
    return successful_downloads


def download_audio_only(url, output_dir="downloads", format='mp3'):
    """Download audio only as MP3 or WAV"""
    ffmpeg_path, ffprobe_path = check_ffmpeg_installed()
    if not ffmpeg_path or not ffprobe_path:
        return None

    # Get the directory containing ffmpeg
    ffmpeg_dir = os.path.dirname(ffmpeg_path)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format,
        }],
        'ffmpeg_location': ffmpeg_dir,
        'quiet': False,
        'no_warnings': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = os.path.splitext(ydl.prepare_filename(info))[0] + f'.{format}'
            print(f"✅ Downloaded: {filename}")
            return filename
    except Exception as e:
        print(f"❌ Error downloading audio: {e}")
        return None


def download_best_video(url, output_dir="downloads"):
    """Download best video with audio"""
    ffmpeg_path, ffprobe_path = check_ffmpeg_installed()
    if not ffmpeg_path or not ffprobe_path:
        return None

    # Get the directory containing ffmpeg
    ffmpeg_dir = os.path.dirname(ffmpeg_path)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'ffmpeg_location': ffmpeg_dir,
        'quiet': False,
        'no_warnings': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            print(f"✅ Downloaded: {filename}")
            return filename
    except Exception as e:
        print(f"❌ Error downloading video: {e}")
        return None


def download_youtube_media_url(url, output_dir="downloads"):
    """Download media for a specific URL with format selection"""
    # Get available formats
    formats, info = get_available_formats(url)
    if not formats:
        print("❌ Could not retrieve available formats")
        return None

    # Let user select format
    selected_format = format_selection_menu(formats, info)
    if not selected_format:
        return None

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get the directory containing ffmpeg
    ffmpeg_path, _ = check_ffmpeg_installed()
    if not ffmpeg_path:
        return None
    ffmpeg_dir = os.path.dirname(ffmpeg_path)

    # Set download options based on selection
    format_id = selected_format.get('format_id')
    ext = selected_format.get('ext')

    # Use sanitized title for filename
    default_filename = sanitize_filename(info.get('title', 'video'))
    filename = os.path.join(output_dir, f"{default_filename}.%(ext)s")

    ydl_opts = {
        'format': format_id,
        'outtmpl': filename,
        'ffmpeg_location': ffmpeg_dir,
        'quiet': False,
        'no_warnings': False,
    }

    # If it's an audio format, add postprocessing options
    if selected_format.get('vcodec') == 'none':
        # Ask for audio format preference
        print("\n🎵 Audio format options:")
        print("1. MP3 (most compatible)")
        print("2. WAV (lossless, large file)")
        print("3. Keep original format")

        audio_choice = input("Select audio format (1-3, press Enter for MP3): ").strip()
        if audio_choice == "2":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }]
            ext = 'wav'
        elif audio_choice == "3":
            # Keep original format
            pass
        else:  # Default to MP3
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            ext = 'mp3'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # Get the actual filename that was saved
            final_filename = os.path.splitext(ydl.prepare_filename(info))[0] + f'.{ext}'

            print(f"✅ Downloaded: {final_filename}")
            return final_filename

    except Exception as e:
        print(f"❌ Error downloading media: {e}")
        return None


def download_wav_audio():
    """Direct function to download audio as WAV"""
    ffmpeg_path, ffprobe_path = check_ffmpeg_installed()
    if not ffmpeg_path or not ffprobe_path:
        return None

    url = input("Enter YouTube URL: ").strip()
    if not url:
        print("❌ Please enter a URL")
        return None

    output_dir = input("📁 Enter output directory (press Enter for 'downloads'): ").strip()
    output_dir = output_dir if output_dir else "downloads"
    os.makedirs(output_dir, exist_ok=True)

    # Get the directory containing ffmpeg
    ffmpeg_dir = os.path.dirname(ffmpeg_path)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'ffmpeg_location': ffmpeg_dir,
        'quiet': False,
        'no_warnings': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = os.path.splitext(ydl.prepare_filename(info))[0] + '.wav'
            print(f"✅ Downloaded WAV: {filename}")
            return filename
    except Exception as e:
        print(f"❌ Error downloading WAV audio: {e}")
        return None


if __name__ == "__main__":
    print("YouTube Media Downloader")
    print("=" * 50)

    while True:
        print("\nChoose an option:")
        print("1. Download single video/audio (with format selection)")
        print("2. Batch download from file")
        print("3. Download best video quality")
        print("4. Download audio only (MP3)")
        print("5. Download audio only (WAV)")
        print("6. Exit")

        choice = input("Enter choice (1-6): ").strip()

        if choice == "1":
            result = download_youtube_media()
        elif choice == "2":
            result = batch_download()
        elif choice == "3":
            url = input("Enter YouTube URL: ").strip()
            result = download_best_video(url)
        elif choice == "4":
            url = input("Enter YouTube URL: ").strip()
            result = download_audio_only(url, format='mp3')
        elif choice == "5":
            result = download_wav_audio()
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")
            continue

        if result:
            print(f"✨ Operation completed successfully")
        else:
            print("❌ Operation failed")
