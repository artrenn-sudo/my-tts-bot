# cogs/voice_channel.py
import discord
from discord.ext import commands
from discord import app_commands

class VoiceChannelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="voice_channels", description="List all voice channels in the server.")
    async def voice_channels(self, interaction: discord.Interaction):
        voice_channels = [vc for vc in interaction.guild.voice_channels]
        if not voice_channels:
            await interaction.response.send_message("No voice channels found.")
            return

        description = "\n".join([f"- {vc.name} ({len(vc.members)} members)" for vc in voice_channels])
        embed = discord.Embed(title="🎙️ Voice Channels", description=description, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

# Setup
async def setup(bot):
    await bot.add_cog(VoiceChannelCog(bot))
