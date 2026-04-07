# 📥 Discord Media Downloader Bot

Ein performanter, moderner Discord-Bot zum Herunterladen von Videos, Audio und Thumbnails über `yt-dlp`. 

## ✨ Features
- 🎬 **Video:** MP4-Format mit bestmöglicher Qualität (gemerged Video + Audio).
- 🎵 **Audio:** Extraktion in MP3.
- 🖼️ **Thumbnails:** Extrahieren und Speichern von Vorschaubildern (als PNG).
- ⚡ **Non-Blocking:** Der Bot friert während langer Downloads nicht ein.
- 🧹 **Auto-Cleanup:** Automatisierte lokale Dateiverwaltung, um Speicher zu sparen.
- 📱 **Modern UI:** Volle Steuerung über interaktive Slash-Commands und Dropdown-Menüs.

---

## 🚀 Deployment auf Ubuntu (Docker) - Empfohlen!

Die absolut beste und wartungsfreieste Methode, diesen Bot auf einem Server zu betreiben, ist **Docker**. Dadurch packst du Python und zwingende Betriebssystem-Pakete wie `ffmpeg` in einen sauberen Container ("Works on my machine"-Prinzip).

### Voraussetzungen
Dein Server benötigt **Docker** und **Docker Compose**.
Auf einem frischen Ubuntu-Server installierst du beides so:
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
```

### 1. Installation
1. Klone das von dir auf GitHub hochgeladene Repository auf den Server:
   ```bash
   git clone <DEINE_GITHUB_REPO_URL>
   cd discord-downloader-bot
   ```
2. Kopiere die Beispiel-Umgebungsdatei:
   ```bash
   cp .env.example .env
   ```
3. Trag deinen Bot Token in die soeben erstellte Datei ein:
   ```bash
   nano .env
   # DISCORD_BOT_TOKEN einfügen und speichern via STRG+O -> STRG+X
   ```

### 2. Starten
Führe diesen Befehl aus, um den Bot im Hintergrund des Servers hochzufahren:
```bash
sudo docker-compose up -d --build
```

### 3. Log-Ausgabe prüfen
Um zu sehen ob der Bot online ist oder gerade etwas herunterlädt:
```bash
sudo docker-compose logs -f
```

---

## 💻 Lokale Entwicklung

Falls du keinen Docker nutzt und das Ganze manuell starten willst:

1. Installiere **Python 3.10+** und zwingend **FFmpeg** auf deinem Rechner.
2. Füge den FFmpeg `bin`-Ordner deinen Umgebungsvariablen (System Path) hinzu.
3. Installiere alle benötigten Pakete:
   ```bash
   pip install -r requirements.txt
   ```
4. Lege eine `.env` Datei an (oder kopier `.env.example`) und befülle `DISCORD_BOT_TOKEN`.
5. Starte den Bot:
   ```bash
   python bot.py
   ```
