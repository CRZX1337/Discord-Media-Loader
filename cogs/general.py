import discord
from discord.ext import commands
import yt_dlp as _ydl
from ui import DashboardView
from constants import BOT_NAME, VERSION

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_cmd(self, ctx):
        is_admin = ctx.author.guild_permissions.administrator
        embed = discord.Embed(
            title=f"📖 {BOT_NAME} — Commands",
            description="All available commands:",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="🎛️ General",
            value=(
                "`!help` — Show this overview\n"
                "`!dashboard` — Re-post the download dashboard\n"
                "`!status` — Show bot status and yt-dlp version"
            ),
            inline=False
        )
        if is_admin:
            embed.add_field(
                name="🔧 Admin Only",
                value=(
                    "`!update-ytdlp` — Update yt-dlp to the latest version\n"
                    "`!cleanup` — Force-delete all files in the downloads folder"
                ),
                inline=False
            )
        embed.set_footer(text=f"{BOT_NAME} v{VERSION}")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="status")
    async def status_cmd(self, ctx):
        ytdlp_version = _ydl.version.__version__
        embed = discord.Embed(title=f"📊 {BOT_NAME} — Status", color=discord.Color.green())
        embed.add_field(name="🤖 Bot", value="Online ✅", inline=True)
        embed.add_field(name="📦 yt-dlp", value=f"`{ytdlp_version}`", inline=True)
        embed.add_field(name="🐍 Version", value=f"{BOT_NAME} v{VERSION}", inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="dashboard")
    async def dashboard_cmd(self, ctx):
        await ctx.send(
            content="Here is your permanent dashboard for media tasks!",
            view=DashboardView()
        )
