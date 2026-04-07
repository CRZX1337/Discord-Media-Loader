import os
import glob
import re
import uuid
import yt_dlp

def sanitize_filename(name: str) -> str:
    """Removes invalid or problematic characters from a filename."""
    # Allow only letters, numbers, hyphens, underscores, and dots
    name = re.sub(r'[^\w\s\-\.]', '', name)
    # Replace spaces (incl. tabs etc.) with underscores for better OS compatibility
    name = re.sub(r'\s+', '_', name)
    # Remove excessive characters at the beginning/end
    return name.strip('_.-')

def download_media(url: str, format_type: str, quality: str = "1080", status_hook: callable = None) -> str:
    """
    Downloads files synchronously via yt-dlp with live status updates.
    """
    temp_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generate unique ID for collision-free downloads
    unique_id = str(uuid.uuid4())[:8]
    filepath_prefix = os.path.join(temp_dir, f'%(title)s_{unique_id}')
    
    # Internal flag to ensure we only send a status update once per phase
    current_phase = {"value": "SEARCHING"}
    
    def progress_handler(d):
        if status_hook:
            if d['status'] == 'downloading' and current_phase["value"] != "DOWNLOADING":
                current_phase["value"] = "DOWNLOADING"
                status_hook("DOWNLOADING")
            elif d['status'] == 'finished' and current_phase["value"] != "PROCESSING":
                current_phase["value"] = "PROCESSING"
                status_hook("PROCESSING")

    ydl_opts = {
        'outtmpl': f'{filepath_prefix}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [progress_handler],
    }
    
    # Quality Mapping
    quality_map = {
        "720": "bestvideo[height<=720]+bestaudio/best",
        "1080": "bestvideo[height<=1080]+bestaudio/best",
        "1440": "bestvideo[height<=1440]+bestaudio/best",
        "2160": "bestvideo[height<=2160]+bestaudio/best"
    }
    
    if format_type == "video":
        ydl_opts['format'] = quality_map.get(quality, quality_map["1080"])
        ydl_opts['merge_output_format'] = 'mp4'
    elif format_type == "audio":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif format_type == "picture":
        ydl_opts['skip_download'] = True
        ydl_opts['writethumbnail'] = True
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegThumbnailsConvertor',
            'format': 'png',
        }]

    try:
        if status_hook:
            status_hook("SEARCHING")
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
            
        # Search for file via the unique pattern ID
        files = glob.glob(os.path.join(temp_dir, f"*_{unique_id}.*"))
        
        if not files:
            raise Exception("No destination file generated. The post might be private, or the platform blocked the request.")
            
        # Push the latest modified file to the top
        files.sort(key=os.path.getmtime, reverse=True)
        original_file = files[0]
        
        # Convert original name into a safe name
        dirname, basename = os.path.split(original_file)
        name_only, ext = os.path.splitext(basename)
        
        sanitized_name = sanitize_filename(name_only) + ext
        sanitized_path = os.path.join(dirname, sanitized_name)
        
        # Rename file to prevent Server/Discord issues with emojis or blank spaces
        if original_file != sanitized_path:
            os.rename(original_file, sanitized_path)
            
        return sanitized_path
        
    except Exception as e:
        # Emergency Cleanup, in case yt_dlp leaves broken fragments
        try:
            for tmp_file in glob.glob(os.path.join(temp_dir, f"*_{unique_id}.*")):
                os.remove(tmp_file)
        except Exception:
            pass
        raise e
