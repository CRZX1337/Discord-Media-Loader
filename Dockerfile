# Verwende ein leichtgewichtiges Python-Image
FROM python:3.11-slim

# Installiere FFmpeg (zwingend erforderlich für yt-dlp Video/Audio Merging)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Setze das Arbeitsverzeichnis
WORKDIR /app

# Kopiere die requirements und installiere Abhängigkeiten (Layer-Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den restlichen Code
COPY downloader.py ui.py main.py ./

# Führe den Bot aus
CMD ["python", "main.py"]
