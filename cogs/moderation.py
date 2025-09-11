# cogs/moderation.py

import discord
from discord.ext import commands
from discord import app_commands
from utils.permissions import has_guild_permissions

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Ban a member.")
    @has_guild_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return

        try:
            await interaction.guild.ban(member, reason=reason)
            await interaction.response.send_message(f"✅ {member.mention} has been banned. Reason: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to ban: {e}", ephemeral=True)

    @app_commands.command(name="kick", description="Kick a member.")
    @has_guild_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return

        try:
            await interaction.guild.kick(member, reason=reason)
            await interaction.response.send_message(f"✅ {member.mention} has been kicked. Reason: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to kick: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
