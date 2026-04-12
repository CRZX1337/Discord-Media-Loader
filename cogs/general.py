import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp as _ydl
from ui import DashboardView
from constants import BOT_NAME, VERSION


def _get_dashboard_embed():
    """Import lazily to avoid circular imports."""
    from main import build_dashboard_embed
    return build_dashboard_embed()


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
                "`!status` — Show bot status and yt-dlp version\n"
                "`/ping` — Check bot latency"
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
        import instaloader as _il
        ytdlp_version = _ydl.version.__version__
        il_version = getattr(_il, '__version__', 'unknown')
        embed = discord.Embed(title=f"📊 {BOT_NAME} — Status", color=discord.Color.green())
        embed.add_field(name="🤖 Bot", value="Online ✅", inline=True)
        embed.add_field(name="📦 yt-dlp", value=f"`{ytdlp_version}`", inline=True)
        embed.add_field(name="📸 instaloader", value=f"`{il_version}`", inline=True)
        embed.add_field(name="🐍 Version", value=f"{BOT_NAME} v{VERSION}", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="dashboard")
    async def dashboard_cmd(self, ctx):
        channel = ctx.channel
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if channel.permissions_for(channel.guild.me).manage_messages:
            try:
                await channel.purge(limit=50, check=lambda m: m.author == self.bot.user)
            except Exception:
                pass

        await channel.send(embed=_get_dashboard_embed(), view=DashboardView())

    @app_commands.command(name="ping", description="Check bot latency and connection status")
    async def ping(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)

        if latency_ms < 100:
            color = discord.Color.green()
            status = "🟢 Excellent"
        elif latency_ms < 300:
            color = discord.Color.yellow()
            status = "🟡 Good"
        else:
            color = discord.Color.red()
            status = "🔴 High"

        embed = discord.Embed(
            title="🏓 Pong!",
            color=color
        )
        embed.add_field(name="WebSocket Latency", value=f"`{latency_ms}ms`", inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        embed.set_footer(text=f"{BOT_NAME} v{VERSION}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(General(bot))
