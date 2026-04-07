import os
import asyncio
import logging
import discord
import json

from downloader import download_media, get_media_info

logger = logging.getLogger("MediaBot")

# Load config for BASE_URL
try:
    with open("config.json", "r") as f:
        CONFIG = json.load(f)
except Exception:
    CONFIG = {"BASE_URL": "http://localhost:8080"}

async def start_analysis(interaction: discord.Interaction, url: str, format_requested: str):
    """Core logic to analyze a link and present the next selection view."""
    # If the interaction hasn't been responded to yet (button case)
    if not interaction.response.is_done():
        await interaction.response.send_message("🔍 **Analyzing content...** Please wait.", ephemeral=True)
    else:
        # Otherwise update the existing message (modal case)
        await interaction.edit_original_response(content="🔍 **Analyzing content...** Please wait.", view=None)
    
    info = await asyncio.to_thread(get_media_info, url)
    
    if not info:
        await interaction.edit_original_response(content="❌ **Link Analysis Failed.** I couldn't find any media there! 🤔")
        return

    title_short = info['title'][:50] + "..." if len(info['title']) > 50 else info['title']
    
    if format_requested == "video":
        view = QualitySelectView(url, info['heights'])
        await interaction.edit_original_response(content=f"🎬 **Found:** *{title_short}*\nSelect Your Video Quality:", view=view)
    elif format_requested == "audio":
        view = AudioFormatView(url)
        await interaction.edit_original_response(content=f"🎵 **Found:** *{title_short}*\nSelect Audio Format:", view=view)
    elif format_requested == "picture":
        view = PictureFormatView(url)
        await interaction.edit_original_response(content=f"🖼️ **Found:** *{title_short}*\nSelect Image Format:", view=view)

class QualitySelectView(discord.ui.View):
    """Dynamic quality selection for Videos."""
    def __init__(self, url: str, heights: list):
        super().__init__(timeout=180)
        self.url = url
        
        options = []
        standard_heights = [360, 480, 720, 1080, 1440, 2160]
        available_standard = [h for h in standard_heights if h <= max(heights or [2160])]
        
        for h in available_standard:
            label = f"{h}p"
            if h == 1080: label += " (Full HD)"
            if h == 2160: label += " (Ultra HD 4K)"
            options.append(discord.SelectOption(label=label, value=str(h)))
        
        if not options:
            options.append(discord.SelectOption(label="Best Available", value="best"))

        self.add_item(self.create_select(options))

    def create_select(self, options):
        select = discord.ui.Select(placeholder="Choose video quality...", options=options)
        select.callback = self.on_select
        return select

    async def on_select(self, interaction: discord.Interaction):
        quality = interaction.data['values'][0]
        await process_action(interaction, self.url, "video", quality=quality)

class AudioFormatView(discord.ui.View):
    """Format selection for Audio."""
    def __init__(self, url: str):
        super().__init__(timeout=180)
        self.url = url

    @discord.ui.select(
        placeholder="Choose audio format...",
        options=[
            discord.SelectOption(label="MP3 (Standard)", value="mp3"),
            discord.SelectOption(label="WAV (Lossless)", value="wav"),
            discord.SelectOption(label="FLAC (High Fidelity)", value="flac"),
            discord.SelectOption(label="M4A (Apple)", value="m4a")
        ]
    )
    async def select_format(self, interaction: discord.Interaction, select: discord.ui.Select):
        await process_action(interaction, self.url, "audio", extension=select.values[0])

class PictureFormatView(discord.ui.View):
    """Format selection for Pictures."""
    def __init__(self, url: str):
        super().__init__(timeout=180)
        self.url = url

    @discord.ui.select(
        placeholder="Choose image format...",
        options=[
            discord.SelectOption(label="PNG (Lossless)", value="png"),
            discord.SelectOption(label="JPG (Fast)", value="jpg"),
            discord.SelectOption(label="WEBP (Modern)", value="webp")
        ]
    )
    async def select_format(self, interaction: discord.Interaction, select: discord.ui.Select):
        await process_action(interaction, self.url, "picture", extension=select.values[0])

async def process_action(interaction: discord.Interaction, url: str, format_type: str, quality: str = "1080", extension: str = None):
    # (Existing implementation of process_action remains the same)
    embed = discord.Embed(
        title="📥 Fetchy | Working...",
        description="🔍 Initializing request...",
        color=discord.Color.yellow()
    )
    # Check if we are responding to a selection interaction or updating status
    if not interaction.response.is_done():
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.edit_original_response(embed=embed, view=None)

    loop = interaction.client.loop

    async def update_status_ui(phase):
        phase_map = {
            "SEARCHING": "🔍 Locating media...",
            "DOWNLOADING": "📥 Downloading data...",
            "PROCESSING": "⚙️ Optimizing and skinning..."
        }
        embed.description = phase_map.get(phase, phase)
        await interaction.edit_original_response(embed=embed)

    def status_callback(status):
        asyncio.run_coroutine_threadsafe(update_status_ui(status), loop)

    file_path = None
    try:
        file_path = await asyncio.to_thread(download_media, url, format_type, quality, extension, status_callback)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        if file_size_mb > 10.0:
            base_url = CONFIG.get("BASE_URL", "http://localhost:8080").rstrip('/')
            filename = os.path.basename(file_path)
            download_link = f"{base_url}/dl/{filename}"
            embed.title = "📦 File is too large for Discord!"
            embed.description = (
                f"Your file is **{file_size_mb:.2f} MB**. I've hosted it privately for you.\n\n"
                f"🚀 **Download Link:** [Click here to download]({download_link})\n\n"
                "*Link expires in 24 hours.*"
            )
            embed.color = discord.Color.blue()
            await interaction.edit_original_response(embed=embed)
        else:
            embed.title = "✅ Success!"
            embed.description = "Your file has been prepared. Enjoy! ✨"
            embed.color = discord.Color.green()
            discord_file = discord.File(file_path)
            await interaction.edit_original_response(embed=embed, attachments=[discord_file])

    except Exception as e:
        logger.error(f"Download error: {e}")
        embed.title = "❌ Error"
        embed.description = "I couldn't process this link. Please ensure it's public and valid. 😓"
        embed.color = discord.Color.red()
        await interaction.edit_original_response(embed=embed)
    finally:
        if file_path and os.path.exists(file_path):
            if os.path.getsize(file_path) / (1024 * 1024) <= 10.0:
                os.remove(file_path)

class DownloadModal(discord.ui.Modal):
    def __init__(self, format_requested: str):
        super().__init__(title='Analyze Media Link')
        self.format_requested = format_requested

    url_input = discord.ui.TextInput(
        label='Paste Link Here',
        placeholder='YouTube, TikTok, X, Instagram...',
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await start_analysis(interaction, self.url_input.value, self.format_requested)

class DashboardView(discord.ui.View):
    def __init__(self, url: str = None):
        super().__init__(timeout=None)
        self.url = url

    @discord.ui.button(label="🎥 Video", style=discord.ButtonStyle.primary, custom_id="fetchy_video")
    async def video(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.url:
            await start_analysis(interaction, self.url, "video")
        else:
            await interaction.response.send_modal(DownloadModal("video"))

    @discord.ui.button(label="🎵 Audio", style=discord.ButtonStyle.success, custom_id="fetchy_audio")
    async def audio(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.url:
            await start_analysis(interaction, self.url, "audio")
        else:
            await interaction.response.send_modal(DownloadModal("audio"))

    @discord.ui.button(label="🖼️ Picture", style=discord.ButtonStyle.secondary, custom_id="fetchy_picture")
    async def picture(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.url:
            await start_analysis(interaction, self.url, "picture")
        else:
            await interaction.response.send_modal(DownloadModal("picture"))
