# cogs/ai.py
import discord
from discord.ext import commands
from discord import app_commands
import os
import openai
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ask", description="Ask the bot anything!")
    async def ask(self, interaction: discord.Interaction, *, question: str):
        await interaction.response.defer()

        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": question}]
            )

            answer = response.choices[0].message.content

            chunks = [answer[i:i+1990] for i in range(0, len(answer), 1990)]

            await interaction.followup.send(f"**❓ You asked:**\n`{question}`")

            for chunk in chunks:
                await interaction.followup.send(chunk)

        except Exception as e:
            await interaction.followup.send("An error occurred while fetching a response.")
            print(f"AI error: {e}")

# Setup
async def setup(bot):
    await bot.add_cog(AICog(bot))
