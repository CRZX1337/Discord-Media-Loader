# 📥 Discord Media Downloader Bot

A high-performance, modern Discord bot for downloading Videos, Audio, and Pictures using `yt-dlp`. 

## ✨ Features
- 🎬 **Video:** MP4 format in the highest possible quality (merged Video + Audio).
- 🎵 **Audio:** Extracted straight to MP3.
- 🖼️ **Pictures:** Extracts and saves media preview pictures (as PNG).
- ⚡ **Non-Blocking:** The bot stays responsive during long downloads.
- 🧹 **Auto-Cleanup:** Automated local file management to save disk space.
- 📱 **Modern UI:** Full control over interactive Slash-Commands and slick UI dropdowns/buttons.

---

## 🚀 Deployment on Ubuntu (Docker) - Recommended!

The absolute best and lowest-maintenance way to run this bot is via **Docker**. This packages Python and required system dependencies like `ffmpeg` into a clean container ("Works on my machine" principle).

### Prerequisites
Your server requires **Docker** and **Docker Compose**.
On a fresh Ubuntu setup, install them like this:
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
```

### 1. Installation
1. Clone your GitHub repository onto your server:
   ```bash
   git clone <YOUR_GITHUB_REPO_URL>
   cd discord-downloader-bot
   ```
2. Copy the boilerplate environment file:
   ```bash
   cp .env.example .env
   ```
3. Type your Bot Token into the newly created file:
   ```bash
   nano .env
   # Insert DISCORD_BOT_TOKEN and save via CTRL+O -> Enter -> CTRL+X
   ```

### 2. Startup
Run this command to boot the bot gracefully in the background:
```bash
sudo docker-compose up -d --build
```
*(Alternatively, just run `./update.sh`!)*

### 3. Check Logs
To see if the bot is online or actively downloading stuff:
```bash
sudo docker-compose logs -f
```

---

## 💻 Local Development

If you prefer avoiding Docker for local tests:

1. Install **Python 3.10+** and mandatory **FFmpeg** on your machine.
2. Add the FFmpeg `bin` folder to your system's Environment Variables (System Path).
3. Install all required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file (or copy `.env.example`) and supply your `DISCORD_BOT_TOKEN`.
5. Run your bot smoothly:
   ```bash
   python main.py
   ```
