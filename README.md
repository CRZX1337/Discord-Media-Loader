# 🚀 Fetchy — Your Personal Media Assistant

Fetchy is a high-performance, privacy-focused Discord bot designed to download and manage media from various platforms seamlessly. Built with a modern modular architecture, Fetchy provides a clean, persistent dashboard for all your extraction needs.

## ✨ Key Features

- 🎬 **Video Extraction:** High-quality MP4 downloads with automatic merging.
- 🎵 **Audio Extraction:** High-fidelity MP3 conversion for your favorite tracks.
- 🖼️ **Picture Extraction:** High-resolution preview image extraction (PNG).
- ⚡ **Asynchronous Processing:** Non-blocking downloads ensure the bot stays responsive.
- 🛡️ **Privacy Centric:** Completely anonymous interactions with automatic ephemeral responses.
- 🧹 **Automated Infrastructure:** Built-in disk cleanup and Docker support for a maintenance-free experience.

---

## 🚀 Getting Started

### 📦 Docker Deployment (Recommended)
The most efficient way to run Fetchy is using Docker. This ensures a consistent environment with all dependencies (like FFmpeg) pre-configured.

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/CRZX1337/Fetchy
   cd Fetchy
   ```

2. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your DISCORD_BOT_TOKEN
   ```

3. **Deploy:**
   ```bash
   sudo docker compose up -d --build
   ```

---

### 💻 Local Installation
If you prefer to run the system directly on your host machine:

1. **System Requirements:**
   - Python 3.10+
   - **FFmpeg** (Must be in your system PATH)

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application:**
   ```bash
   python main.py
   ```

---

## 🛠️ How to Use
Fetchy utilizes a centralized **Dashboard** for a clean user experience:

1. **Navigate** to your designated dashboard channel.
2. **Select your format** using the interactive buttons (Video, Audio, or Picture).
3. **Submit your link** in the secure modal popup.
4. **Download** your file directly from the ephemeral response.

## 📜 Credits & Stack
Fetchy is powered by these amazing open-source projects:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — High-performance media extraction.
- [discord.py](https://github.com/Rapptz/discord.py) — Modern Discord API wrapper for Python.
- [Docker](https://www.docker.com/) — Containerization and infrastructure.

---
*Developed with care by [CRZX1337](https://github.com/CRZX1337)*
