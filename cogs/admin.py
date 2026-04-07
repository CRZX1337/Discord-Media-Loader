import discord
from discord.ext import commands
import os
import asyncio

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cleanup")
    @commands.has_permissions(administrator=True)
    async def cleanup_cmd(self, ctx):
        msg = await ctx.reply("🧹 Running cleanup...", mention_author=False)
        count = 0
        if os.path.exists("downloads"):
            for filename in os.listdir("downloads"):
                file_path = os.path.join("downloads", filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        count += 1
                except Exception:
                    pass
        await msg.edit(content=f"✅ Cleanup done — deleted **{count}** file(s).")

    @commands.command(name="update-ytdlp")
    @commands.has_permissions(administrator=True)
    async def update_ytdlp_cmd(self, ctx):
        msg = await ctx.reply("🔄 Updating yt-dlp...", mention_author=False)
        proc = await asyncio.create_subprocess_exec(
            "pip", "install", "--upgrade", "yt-dlp",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            version_line = [l for l in stdout.decode().splitlines() if "Successfully installed" in l]
            info = version_line[0] if version_line else "yt-dlp is already up to date."
            await msg.edit(content=f"✅ {info}")
        else:
            await msg.edit(content=f"❌ Update failed:\n```{stderr.decode()[:500]}```")

    @cleanup_cmd.error
    @update_ytdlp_cmd.error
    async def admin_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ You need administrator permissions for this command.", mention_author=False)
