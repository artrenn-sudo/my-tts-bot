# cogs/voice_channel_manager.py

import discord
from discord.ext import commands
from discord import app_commands
from utils.permissions import has_guild_permissions

class VoiceChannelManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="move", description="Move a member to your current voice channel.")
    @has_guild_permissions(move_members=True)
    async def move(self, interaction: discord.Interaction, member: discord.Member):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ You must be in a voice channel.", ephemeral=True)
            return

        if not member.voice or not member.voice.channel:
            await interaction.response.send_message("❌ The target member is not in a voice channel.", ephemeral=True)
            return

        try:
            await member.move_to(interaction.user.voice.channel)
            await interaction.response.send_message(
                f"✅ Moved {member.mention} to **{interaction.user.voice.channel.name}**."
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to move member: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(VoiceChannelManagerCog(bot))
