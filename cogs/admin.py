# cogs/admin.py

import discord
from discord.ext import commands
from discord import app_commands
from utils.permissions import has_guild_permissions

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sync", description="Sync all slash commands.")
    @has_guild_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
        try:
            synced = await self.bot.tree.sync()
            await interaction.response.send_message(f"✅ Synced {len(synced)} commands globally!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to sync: {e}", ephemeral=True)

    @app_commands.command(name="say", description="Make the bot say something.")
    @has_guild_permissions(manage_messages=True)
    async def say(self, interaction: discord.Interaction, *, message: str):
        await interaction.response.send_message("✅ Sent!", ephemeral=True)
        await interaction.channel.send(message)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
