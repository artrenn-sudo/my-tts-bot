import discord
from discord.ext import commands
from discord import app_commands, File
import os
import asyncio
import openai
import requests
from gtts import gTTS
from discord import FFmpegPCMAudio

FFMPEG_PATH = "C:/Users/as/ffmpeg/bin/ffmpeg"

# Load OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

class TTSCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /speak - OpenAI TTS (send audio file only)
    @app_commands.command(name="speak", description="Convert text to speech using OpenAI (file only).")
    async def speak(self, interaction: discord.Interaction, *, text: str):
        await interaction.response.defer()
        try:
            response = openai.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=text
            )
            file_path = "generated/speech.mp3"
            response.stream_to_file(file_path)
            await interaction.followup.send(
                content=f"🗣️ Your input: `{text}`",
                file=File(file_path)
            )
        except Exception as e:
            await interaction.followup.send("❌ Failed to generate speech.")
            print(f"OpenAI TTS error: {e}")

    # Voice greeting / goodbye on_voice_state_update
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        vc = discord.utils.get(self.bot.voice_clients, guild=member.guild)

        if after.channel and vc and after.channel == vc.channel and before.channel != after.channel:
            await self.play_gtts(f"Xin chào {member.display_name}", "greeting.mp3", vc)

        elif before.channel and vc and before.channel == vc.channel and after.channel != vc.channel:
            await self.play_gtts(f"Tạm biệt {member.display_name}", "goodbye.mp3", vc)

    async def play_gtts(self, text: str, filename: str, vc):
        try:
            tts = gTTS(text=text, lang="vi")
            tts.save(filename)

            if vc.is_playing():
                while vc.is_playing():
                    await asyncio.sleep(0.5)

            vc.play(
                FFmpegPCMAudio(filename, executable=FFMPEG_PATH),
                after=lambda e: print(f"✅ Finished playing: {filename}")
            )
        except Exception as e:
            print(f"gTTS playback error: {e}")

async def setup(bot):
    await bot.add_cog(TTSCog(bot))
