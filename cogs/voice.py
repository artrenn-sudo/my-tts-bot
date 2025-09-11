# cogs/voice.py
import discord
from discord.ext import commands
from discord import app_commands

class VoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="join", description="Make the bot join your voice channel.")
    async def join(self, interaction: discord.Interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

        if bot_voice_client:
            await interaction.response.send_message("❌ I'm already in a voice channel.")
            return

        if interaction.user.voice and interaction.user.voice.channel:
            voice_channel = interaction.user.voice.channel
            await voice_channel.connect()
            await interaction.response.send_message(f"🎙️ Joined **{voice_channel.name}**!")
        else:
            await interaction.response.send_message("⚠️ You need to join a voice channel first!")

    @app_commands.command(name="leave", description="Make the bot leave the current voice channel.")
    async def leave(self, interaction: discord.Interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

        if not bot_voice_client:
            await interaction.response.send_message("❌ I'm not in any voice channel.")
            return

        if not interaction.user.voice or interaction.user.voice.channel != bot_voice_client.channel:
            await interaction.response.send_message(f"⚠️ You must be in **{bot_voice_client.channel.name}** to use this command.")
            return

        await bot_voice_client.disconnect()
        await interaction.response.send_message("👋 Left the voice channel.")

# Setup
async def setup(bot):
    await bot.add_cog(VoiceCog(bot))
