#!/bin/bash

echo "🚀 Starte Bot-Update..."

# 1. Neuesten Code von GitHub ziehen
echo "📥 Lade neueste Version herunter..."
git pull

# 2. Docker Images komplett frisch aufbauen (ohne Cache)
echo "🏗️ Baue Docker Container neu auf..."
sudo docker compose build --no-cache

# 3. Docker Container im Hintergrund starten/updaten
echo "🟢 Starte den Bot..."
sudo docker compose up -d

echo "✅ Update erfolgreich abgeschlossen! Der Bot sollte jetzt auf der aktuellsten Version laufen."
