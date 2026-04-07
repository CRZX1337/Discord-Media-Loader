# Use a lightweight Python image
FROM python:3.11-slim

# Install FFmpeg (mandatory for yt-dlp Video/Audio Merging)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements and install dependencies (Layer Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source code
COPY downloader.py ui.py main.py ./

# Start up the Bot
CMD ["python", "main.py"]
