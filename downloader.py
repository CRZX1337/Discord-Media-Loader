import yt_dlp
import os
import uuid
import logging
import re
import time
import threading

# --- LOGGING SETUP ---
logger = logging.getLogger("MediaBot.Downloader")


def _ydl_opts_base() -> dict:
    """Base yt-dlp options shared across all calls."""
    opts = {
        'quiet': True,
        'no_warnings': True,
    }
    if os.path.exists("cookies.txt"):
        opts['cookiefile'] = 'cookies.txt'
    return opts


def get_media_info(url):
    """
    Analyzes a URL to extract title and available video resolutions.
    """
    logger.info(f"Extracting info for {url}")
    try:
        with yt_dlp.YoutubeDL(_ydl_opts_base()) as ydl:
            info = ydl.extract_info(url, download=False)
            heights = []
            if 'formats' in info:
                for f in info['formats']:
                    h = f.get('height')
                    if h and f.get('vcodec') != 'none':
                        heights.append(h)
            return {
                'title': info.get('title', 'Unknown Media'),
                'heights': list(set(heights))
            }
    except Exception as e:
        logger.warning(f"get_media_info failed for {url}: {e}")
        return None


def download_media(url, format_type, quality="1080", extension="mp3", status_hook=None, cancel_event: threading.Event = None):
    """
    Downloads media from a URL based on user preferences.
    Returns (file_path, file_size_mb).
    """
    logger.info(f"Downloading {format_type} from {url} (Quality: {quality}, Ext: {extension})")

    current_phase = {"value": "SEARCHING"}
    last_update = {"time": 0}

    def progress_handler(d):
        if status_hook is None:
            return
        now = time.time()
        if d['status'] == "downloading":
            if cancel_event and cancel_event.is_set():
                raise Exception("Download cancelled by user.")
            if now - last_update["time"] < 2.0 and current_phase["value"] == "DOWNLOADING":
                return
            last_update["time"] = now
            current_phase["value"] = "DOWNLOADING"
            downloaded = d.get('downloaded_bytes', 0) or 0
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            speed = d.get('speed') or 0
            percent = (downloaded / total * 100) if total > 0 else 0
            status_hook({
                "phase": "DOWNLOADING",
                "percent": round(percent, 1),
                "downloaded_mb": round(downloaded / 1024 / 1024, 1),
                "total_mb": round(total / 1024 / 1024, 1),
                "speed_mb": round(speed / 1024 / 1024, 2) if speed else 0,
            })
        elif d['status'] == "finished":
            if cancel_event and cancel_event.is_set():
                raise Exception("Download cancelled by user.")
            if current_phase["value"] != "PROCESSING":
                current_phase["value"] = "PROCESSING"
                status_hook({"phase": "PROCESSING"})

    os.makedirs("downloads", exist_ok=True)
    unique_id = str(uuid.uuid4())[:8]
    output_tpl = f'downloads/%(title)s_{unique_id}.%(ext)s'

    ydl_opts = _ydl_opts_base()
    ydl_opts.update({
        'restrictfilenames': True,
        'outtmpl': output_tpl,
        'progress_hooks': [progress_handler],
    })

    if format_type == "video":
        ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'
        ydl_opts['merge_output_format'] = 'mp4'
    elif format_type == "audio":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': extension,
            'preferredquality': '192',
        }]
    elif format_type == "picture":
        ydl_opts['writethumbnail'] = True
        ydl_opts['skip_download'] = True
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegThumbnailsConvertor',
            'format': extension,
        }]

    try:
        if status_hook is not None:
            status_hook({"phase": "SEARCHING"})

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=True)

            requested = result.get('requested_downloads')
            if requested and len(requested) > 0:
                actual_path = requested[0].get('filepath')
                if actual_path and os.path.exists(actual_path):
                    file_size_mb = os.path.getsize(actual_path) / (1024 * 1024)
                    logger.info(f"Download complete (requested_downloads): {actual_path} ({file_size_mb:.2f} MB)")
                    return actual_path, file_size_mb

            file_path = ydl.prepare_filename(result)
            base, _ = os.path.splitext(file_path)
            actual_path = file_path
            if format_type == "audio":
                actual_path = f"{base}.{extension}"
            elif format_type == "video":
                actual_path = f"{base}.mp4"
            elif format_type == "picture":
                actual_path = f"{base}.{extension}"

            if os.path.exists(actual_path):
                file_size_mb = os.path.getsize(actual_path) / (1024 * 1024)
                logger.info(f"Download complete (prepare_filename): {actual_path} ({file_size_mb:.2f} MB)")
                return actual_path, file_size_mb

            files = [os.path.join("downloads", f) for f in os.listdir("downloads")]
            if files:
                actual_path = max(files, key=os.path.getmtime)
                file_size_mb = os.path.getsize(actual_path) / (1024 * 1024)
                logger.warning(f"Download complete (mtime fallback): {actual_path} ({file_size_mb:.2f} MB)")
                return actual_path, file_size_mb

            raise Exception("File not found after successful download.")
    except Exception as e:
        logger.error(f"download_media failed: {e}")
        raise e


def get_instagram_carousel(url):
    """
    Extracts carousel/single entries from an Instagram post or reel using yt-dlp.
    Returns a list of dicts: [{'index': 1, 'url': '...', 'title': '...', 'ext': 'jpg', 'media_type': 'image'}, ...]
    No Instaloader / no Instagram account required.
    """
    logger.info(f"Extracting Instagram carousel via yt-dlp for {url}")

    clean_url = re.sub(r'[?&]img_index=\d+', '', url)

    ydl_opts = _ydl_opts_base()
    ydl_opts['extract_flat'] = False

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)

        entries = []
        title = info.get('title', 'Instagram Post')[:100]

        # Playlist = carousel (multiple entries)
        if info.get('_type') == 'playlist' and info.get('entries'):
            logger.info(f"Carousel detected: {len(info['entries'])} entries")
            for i, entry in enumerate(info['entries'], start=1):
                if not entry:
                    continue
                is_video = bool(entry.get('formats') and any(
                    f.get('vcodec', 'none') != 'none' for f in entry.get('formats', [])
                ))
                # Best direct URL: use the highest quality thumbnail for images, direct url for videos
                if is_video:
                    media_url = entry.get('url') or _best_video_url(entry)
                    ext = 'mp4'
                    media_type = 'video'
                else:
                    media_url = _best_image_url(entry)
                    ext = 'jpg'
                    media_type = 'image'

                if media_url:
                    entries.append({
                        'index': i,
                        'url': media_url,
                        'title': entry.get('title', title)[:100],
                        'ext': ext,
                        'media_type': media_type,
                    })
                    logger.info(f"Carousel entry {i}: {media_type}")
        else:
            # Single post or reel
            logger.info("Single Instagram post/reel detected")
            is_video = bool(info.get('formats') and any(
                f.get('vcodec', 'none') != 'none' for f in info.get('formats', [])
            ))
            if is_video:
                media_url = info.get('url') or _best_video_url(info)
                ext = 'mp4'
                media_type = 'video'
            else:
                media_url = _best_image_url(info)
                ext = 'jpg'
                media_type = 'image'

            if media_url:
                entries.append({
                    'index': 1,
                    'url': media_url,
                    'title': title,
                    'ext': ext,
                    'media_type': media_type,
                })

        logger.info(f"Found {len(entries)} Instagram entries via yt-dlp")
        return entries

    except Exception as e:
        logger.error(f"get_instagram_carousel failed: {e}")
        return []


def _best_video_url(info: dict) -> str | None:
    """Returns the best video URL from a yt-dlp info dict."""
    formats = info.get('formats', [])
    video_formats = [f for f in formats if f.get('vcodec', 'none') != 'none' and f.get('url')]
    if not video_formats:
        return info.get('url')
    return max(video_formats, key=lambda f: f.get('height') or 0).get('url')


def _best_image_url(info: dict) -> str | None:
    """Returns the best image URL from a yt-dlp info dict (thumbnail or direct url)."""
    # For image posts yt-dlp usually puts the URL directly in info['url']
    direct = info.get('url')
    if direct and not direct.endswith('.mp4'):
        return direct
    # Fallback: largest thumbnail
    thumbnails = info.get('thumbnails', [])
    if thumbnails:
        best = max(thumbnails, key=lambda t: (t.get('width') or 0) * (t.get('height') or 0))
        return best.get('url')
    return info.get('thumbnail')


async def download_instagram_photo(url, index=None):
    """
    Downloads one or all media items from an Instagram post/carousel.
    Uses yt-dlp directly to download — no aiohttp, no Instaloader.
    Returns list of file paths.
    """
    import asyncio
    entries = get_instagram_carousel(url)
    if not entries:
        return []

    to_download = entries if index is None else [e for e in entries if e['index'] == index]
    os.makedirs("downloads", exist_ok=True)
    results = []

    for entry in to_download:
        try:
            unique_id = str(uuid.uuid4())[:8]
            ext = entry.get('ext', 'jpg')
            out_path = f"downloads/ig_{entry['index']}_{unique_id}.{ext}"

            ydl_opts = _ydl_opts_base()
            ydl_opts.update({
                'outtmpl': out_path,
                'restrictfilenames': True,
            })

            # yt-dlp needs to re-extract to download; pass the entry URL directly
            entry_url = entry['url']

            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Download directly from CDN URL (already resolved)
                    ydl.download([entry_url])

            await asyncio.to_thread(_download)

            # yt-dlp may adjust extension; find the actual file
            actual = out_path
            if not os.path.exists(actual):
                # Search for file matching the unique_id prefix
                candidates = [
                    os.path.join("downloads", f)
                    for f in os.listdir("downloads")
                    if unique_id in f
                ]
                if candidates:
                    actual = candidates[0]

            if os.path.exists(actual):
                results.append(actual)
                logger.info(f"Downloaded Instagram entry {entry['index']}: {actual}")
            else:
                logger.warning(f"File not found after download for entry {entry['index']}")

        except Exception as e:
            logger.error(f"Failed to download Instagram entry {entry['index']}: {e}")

    return results
