# cogs/utility.py
import discord
import time
from discord.ext import commands
from discord import app_commands

class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check bot latency.")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latency: **{latency} ms**")

    @app_commands.command(name="userinfo", description="Get info about a user.")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(title=f"User Info: {member}", color=discord.Color.blue())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else discord.Embed.Empty)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Name", value=member.name)
        embed.add_field(name="Display Name", value=member.display_name)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "Unknown")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Get info about the server.")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"Server Info: {guild.name}", color=discord.Color.green())
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        embed.add_field(name="ID", value=guild.id)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown")
        embed.add_field(name="Member Count", value=guild.member_count)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        await interaction.response.send_message(embed=embed)

# Setup
async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
