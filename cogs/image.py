import discord
from discord.ext import commands
from discord import app_commands, File
import os
import openai
import requests

# Load OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

class ImageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="generate_image", description="Generate an image based on a prompt.")
    async def generate_image(self, interaction: discord.Interaction, *, prompt: str):
        await interaction.response.defer()
        try:
            # Gọi OpenAI API để generate image
            response = openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            image_url = response.data[0].url

            # Tải image về
            image_data = requests.get(image_url).content
            image_path = "generated/generated_image.png"
            with open(image_path, "wb") as f:
                f.write(image_data)

            # Gửi image cho user
            await interaction.followup.send(
                content=f"**🖼️ Prompt:** `{prompt}`",
                file=File(image_path)
            )
        except Exception as e:
            await interaction.followup.send("❌ Failed to generate an image.")
            print(f"Error generating image: {e}")

async def setup(bot):
    await bot.add_cog(ImageCog(bot))
