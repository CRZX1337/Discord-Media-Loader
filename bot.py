import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os
import uuid
import glob
import logging
from dotenv import load_dotenv

# Lade lokale .env Datei in die Umgebungsvariablen
load_dotenv()

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MediaBot")

# --- BOT SETUP ---
class MediaBot(commands.Bot):
    def __init__(self):
        # Intents definieren (für einfache Slash-Commands reichen die Standard-Intents vollkommen)
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        # Slash-Commands mit Discord synchronisieren
        await self.tree.sync()
        logger.info("Slash Commands wurden erfolgreich synchronisiert.")

    async def on_ready(self):
        logger.info(f"Bot ist online als {self.user} (ID: {self.user.id})")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="/download"))

bot = MediaBot()

# --- HELPER FUNKTION ---
def download_media(url: str, format_type: str) -> str:
    """
    Diese Hilfsfunktion lädt Dateien via yt-dlp synchron herunter.
    Da yt-dlp blockierend ist, wird diese Funktion vom Bot-Prozess
    in einem separaten Thread via asyncio.to_thread aufgerufen.
    """
    # Eindeutige ID für diesen Download-Job generieren, um Kollisionen zu vermeiden (Thread-Safety)
    job_id = uuid.uuid4().hex
    temp_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Basis-Pfad für diesen Job erstellen
    filepath_prefix = os.path.join(temp_dir, job_id)
    
    # Basis-Optionen für yt-dlp
    ydl_opts = {
        'outtmpl': f'{filepath_prefix}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    if format_type == "video":
        # Lade das qualitativ beste Video und Audio herunter und füge sie als MP4 zusammen (erfordert FFmpeg)
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        ydl_opts['merge_output_format'] = 'mp4'
        
    elif format_type == "audio":
        # Nur Audio herunterladen und explizit in MP3 konvertieren (erfordert FFmpeg)
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        
    elif format_type == "thumbnail":
        # Nur das Thumbnail herunterladen
        ydl_opts['skip_download'] = True
        ydl_opts['writethumbnail'] = True
        # Konvertiere das Vorschaubild in PNG-Format für beste Kompatibilität in Discord
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegThumbnailsConvertor',
            'format': 'png',
        }]

    try:
        # Führe den (blockierenden) Download aus
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Sammle alle erzeugten Dateien, die mit unserer job_id beginnen
        files = glob.glob(f"{filepath_prefix}.*")
        
        if not files:
            raise Exception("Der Download konnte keine Zieldatei generieren (Möglicherweise blockiert, privat oder das Limit der Seite erreicht).")
            
        # yt-dlp könnte manchmal Metadaten-Zusätze erzeugen, weshalb wir zur Sicherheit die zuletzt modifizierte nehmen
        files.sort(key=os.path.getmtime, reverse=True)
        return files[0]
        
    except Exception as e:
        # Bei Abbruch oder Fehler sofort alle Fragmente aufräumen
        for tmp_file in glob.glob(f"{filepath_prefix}.*"):
            try:
                os.remove(tmp_file)
            except:
                pass
        raise e

# --- UI KOMPONENTEN ---
class FormatSelect(discord.ui.Select):
    def __init__(self, url: str):
        self.url = url
        # Definition der drei im Dropdown verfügbaren Optionen
        options = [
            discord.SelectOption(label="Video (MP4)", description="Bestes Video + Audio, gemerged.", emoji="🎬", value="video"),
            discord.SelectOption(label="Audio (MP3)", description="Nur Audio extrahieren.", emoji="🎵", value="audio"),
            discord.SelectOption(label="Thumbnail (PNG)", description="Nur das Vorschaubild laden.", emoji="🖼️", value="thumbnail")
        ]
        # Initialisierung
        super().__init__(placeholder="Wähle das gewünschte Format aus...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # 1. UI Update: Deaktiviere das Dropdown, damit Nutzer nicht doppelt klicken und spammen
        self.disabled = True
        selected_format = self.values[0]
        format_labels = {"video": "Video", "audio": "Audio", "thumbnail": "Thumbnail"}
        
        # Hole das bestehende Embed der Nachricht
        embed = interaction.message.embeds[0]
        # Passe das Embed auf den Status "Gelb" / "Bitte warten" an
        embed.title = f"⏳ Download {format_labels[selected_format]}..."
        embed.description = "Bitte warten, der Download wird verarbeitet.\nJe nach Plattform kann das einige Sekunden dauern."
        embed.color = discord.Color.yellow()  
        
        # Editiere die aktuelle Nachricht mit dem geladenen State
        await interaction.response.edit_message(embed=embed, view=self.view)
        
        file_path = None
        try:
            # 2. Ausführung im Thread: Dies garantiert, dass der restliche Bot (Heartbeat/Chat) erreichbar bleibt!
            file_path = await asyncio.to_thread(download_media, self.url, selected_format)
            
            # 3. Datei-Checking auf das Discord 25MB Limit beurteilen
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > 25:
                # Limit gebrochen: Sende Fehler UI
                embed.title = "❌ Download fehlgeschlagen"
                embed.description = f"Die heruntergeladene Datei ist **{file_size_mb:.2f} MB** groß.\nDas Upload-Limit von Discord liegt bei 25 MB."
                embed.color = discord.Color.red()
                await interaction.edit_original_response(embed=embed, view=None)
            else:
                # Limit gehalten: Erfolgsmeldung bereitstellen
                embed.title = "✅ Download erfolgreich!"
                embed.description = f"Dein **{format_labels[selected_format]}** ist erfolgreich verarbeitet worden."
                embed.color = discord.Color.green()
                
                # Datei an die Response anhängen
                discord_file = discord.File(file_path)
                await interaction.edit_original_response(embed=embed, view=None, attachments=[discord_file])
                
        except Exception as e:
            # 4. Error-Handling-UI: z.B. ungültiger Link, blockierte Website etc.
            logger.error(f"Download Error für {self.url}: {str(e)}")
            embed.title = "❌ Es ist ein Fehler aufgetreten"
            embed.description = f"Beim Versuch, das Medium herunterzuladen lief etwas schief:\n```{str(e)[:700]}```"
            embed.color = discord.Color.red()
            await interaction.edit_original_response(embed=embed, view=None)
            
        finally:
            # 5. OS ZWINGENDES CLEANUP - Die Datei MUSS im Code gelöscht werden, um Serverplatz zu sparen.
            # Tritt in JEDEM Fall am Schluss ein, unabhängig von Erfolg oder Error.
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Temporäre Datei erfolgreich gelöscht (Cleanup): {file_path}")
                except Exception as cleanup_err:
                    logger.error(f"Konnte temporäre Datei nicht löschen: {cleanup_err}")

class DownloadView(discord.ui.View):
    def __init__(self, url: str):
        # Timeout bedeutet, nach 3 Minuten lässt sich das Dropdown nicht mehr betätigen
        super().__init__(timeout=180)
        self.add_item(FormatSelect(url))
        
# --- SLASH COMMAND ---
@bot.tree.command(name="download", description="Lade ein Video, Audio oder Thumbnail per yt-dlp herunter.")
@app_commands.describe(url="Der Link zum Medium (YouTube, Twitter, TikTok, Reddit etc.)")
async def download_command(interaction: discord.Interaction, url: str):
    # Initiales Embed der ersten Slash-Command Antwort
    embed = discord.Embed(
        title="📥 Media Downloader",
        description=f"Wähle das Format für folgende URL:\n`{url}`",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Unterstützt YouTube, Reddit, X/Twitter, TikTok uvm.")
    
    view = DownloadView(url)
    
    # Den User initial anpingen und das Dropdown anzeigen
    await interaction.response.send_message(embed=embed, view=view)

# --- BOT ENTRYPOINT ---
if __name__ == "__main__":
    # Hole dir den Bot Token aus den Umgebungsvariablen.
    # Alternativ: Trage ihn hier statisch als String ein z.B. TOKEN = "MTEx..."
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    
    if not TOKEN:
        logger.error("Kein Token im Environment gefunden! Bitte Umgebungsvariable 'DISCORD_BOT_TOKEN' setzen oder Token hartkodieren.")
    else:
        logger.info("Bot wird gestartet...")
        bot.run(TOKEN)
