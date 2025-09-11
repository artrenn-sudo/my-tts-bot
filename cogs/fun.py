# cogs/fun.py
import discord
import random
import requests
from discord.ext import commands
from discord import app_commands

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="joke", description="Get a random joke.")
    async def joke(self, interaction: discord.Interaction):
        url = "https://official-joke-api.appspot.com/random_joke"
        try:
            response = requests.get(url)
            data = response.json()

            setup = data["setup"]
            punchline = data["punchline"]

            await interaction.response.send_message(f"**{setup}**\n||{punchline}||")
        except Exception as e:
            await interaction.response.send_message("Failed to fetch a joke.")
            print(f"Joke error: {e}")

    @app_commands.command(name="coinflip", description="Flip a virtual coin.")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        await interaction.response.send_message(f"🪙 The coin landed on: **{result}**!")

    @app_commands.command(name="meme", description="Get a random meme from Reddit.")
    async def meme(self, interaction: discord.Interaction):
        url = "https://meme-api.com/gimme"
        try:
            response = requests.get(url)
            data = response.json()
            meme_url = data["url"]
            title = data["title"]

            embed = discord.Embed(title=title, color=discord.Color.random())
            embed.set_image(url=meme_url)

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message("Failed to fetch a meme.")
            print(f"Meme error: {e}")

# Setup
async def setup(bot):
    await bot.add_cog(FunCog(bot))
