import os
import random
import asyncio
import requests
import io
import tempfile
import re

import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import File, FFmpegPCMAudio

from gtts import gTTS
from dotenv import load_dotenv
from fpdf import FPDF
from openai import OpenAI
import ctypes.util

# =========[ FFMPEG PATH ]=========
FFMPEG_PATH = os.getenv("FFMPEG_PATH") or (
    r"C:\Users\as\ffmpeg\bin\ffmpeg.exe" if os.name == "nt" else "/usr/bin/ffmpeg"
)

# =========[ OPUS LOAD ]=========
def load_opus_crossplatform():
    """Load libopus cho Windows & Linux (Railway)."""
    if discord.opus.is_loaded():
        return
    if os.name == "nt":
        path = os.getenv("OPUS_PATH") or r"C:\Users\as\my-tts-bot\opus.dll"
    else:
        path = os.getenv("OPUS_PATH") or ctypes.util.find_library("opus") or "libopus.so.0"
    discord.opus.load_opus(path)

try:
    load_opus_crossplatform()
except Exception as e:
    print("Load Opus failed:", e)

print("Opus loaded?", discord.opus.is_loaded())

# =========[ ENV / TOKEN ]=========
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# =========[ DISCORD INTENTS / BOT ]=========
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

# =========[ UTIL ]=========
def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

# =========[ READY ]=========
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"{bot.user} is online and {len(synced)} app commands are synced!")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    try:
        import discord as d
        print("Opus loaded?", d.opus.is_loaded())
        print("discord.py version:", d.__version__)
    except Exception as e:
        print("Check Opus/version failed:", e)

# =========[ VOICE JOIN / LEAVE ]=========
@bot.tree.command(name="join", description="Make the bot join your voice channel.")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("⚠️ Bạn cần vào kênh thoại trước khi gọi bot!", ephemeral=True)
        return

    vc = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if vc:
        try:
            await vc.disconnect(force=True)
        except Exception as e:
            print(f"Force disconnect old VC failed: {e}")

    try:
        channel = interaction.user.voice.channel
        await channel.connect(reconnect=True, timeout=20)
        await interaction.response.send_message(f"🎙️ Đã tham gia **{channel.name}**!")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Bot thiếu quyền **Connect/Speak** trong kênh này.", ephemeral=True)
    except discord.ClientException as e:
        await interaction.response.send_message(f"❌ Không thể vào kênh thoại (ClientException): `{e}`", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Không vào được kênh thoại: `{e}`", ephemeral=True)

@bot.tree.command(name="leave", description="Make the bot leave the current voice channel.")
async def leave(interaction: discord.Interaction):
    bot_voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    if not bot_voice_client:
        await interaction.response.send_message("❌ Tôi hiện không tham gia vào kênh thoại nào.")
        return

    if not interaction.user.voice or interaction.user.voice.channel != bot_voice_client.channel:
        await interaction.response.send_message(f"⚠️ Bạn phải ở trong **{bot_voice_client.channel.name}** để dùng lệnh này.")
        return

    await bot_voice_client.disconnect()
    await interaction.response.send_message("👋 hoi ik day...")

# =========[ MINI GAMES ]=========
rps_games = {}

@bot.tree.command(name="menu", description="Show game command menu")
async def menu(interaction: discord.Interaction):
    await interaction.response.send_message("""
🎮 **Game Menu:**
- `/roll_dice [sides]` or `mtdr` — Roll a dice (default 6 sides)
- `/flip_coin` or `mtfc` — Flip a coin
- `/rps choice:` or `mtrps rock/paper/scissors` — Rock, Paper, Scissors vs bot
- `/rps_challenge @user` or `mtrpsu @user` — Challenge a user
- `/rps_play choice:` or `mtrpsu rock/paper/scissors` — Make your move
""")

@bot.tree.command(name="roll_dice", description="Roll a 6-sided dice with button.")
async def roll_dice(interaction: discord.Interaction):
    class DiceView(View):
        @discord.ui.button(label="Roll 🎲", style=discord.ButtonStyle.primary)
        async def roll_button(self, interaction: discord.Interaction, button: Button):
            result = random.randint(1, 6)
            await interaction.response.edit_message(content=f"🎲 You rolled a **{result}**!", view=self)
    await interaction.response.send_message("Click the button to roll the dice!", view=DiceView())

@bot.tree.command(name="flip_coin", description="Flip a coin with button.")
async def flip_coin(interaction: discord.Interaction):
    class CoinView(View):
        @discord.ui.button(label="Flip 🪙", style=discord.ButtonStyle.secondary)
        async def flip_button(self, interaction: discord.Interaction, button: Button):
            result = random.choice(["Heads", "Tails"])
            await interaction.response.edit_message(content=f"🪙 The coin landed on **{result}**!", view=self)
    await interaction.response.send_message("Click the button to flip a coin!", view=CoinView())

@bot.tree.command(name="rps", description="Play Rock, Paper, Scissors vs the bot.")
async def rps(interaction: discord.Interaction):
    class RPSView(View):
        @discord.ui.button(label="Rock 🪨", style=discord.ButtonStyle.primary)
        async def rock(self, interaction: discord.Interaction, button: Button):
            await self.play(interaction, "rock")
        @discord.ui.button(label="Paper 📄", style=discord.ButtonStyle.success)
        async def paper(self, interaction: discord.Interaction, button: Button):
            await self.play(interaction, "paper")
        @discord.ui.button(label="Scissors ✂️", style=discord.ButtonStyle.danger)
        async def scissors(self, interaction: discord.Interaction, button: Button):
            await self.play(interaction, "scissors")
        async def play(self, interaction: discord.Interaction, user_choice: str):
            bot_choice = random.choice(["rock", "paper", "scissors"])
            if user_choice == bot_choice:
                result = "It's a tie!"
            elif (user_choice == "rock" and bot_choice == "scissors") or \
                 (user_choice == "scissors" and bot_choice == "paper") or \
                 (user_choice == "paper" and bot_choice == "rock"):
                result = "You win!"
            else:
                result = "You lose!"
            await interaction.response.edit_message(
                content=f"You chose **{user_choice}**, I chose **{bot_choice}**. {result}",
                view=self
            )
    await interaction.response.send_message("Choose your move:", view=RPSView())

@bot.tree.command(name="rps_play", description="Play your move in Rock, Paper, Scissors.")
async def rps_play(interaction: discord.Interaction, choice: str):
    user_id = interaction.user.id
    valid_choices = ["rock", "paper", "scissors"]
    choice = choice.lower()

    if choice not in valid_choices:
        await interaction.response.send_message("Invalid choice. Use rock, paper, or scissors.")
        return
    if user_id not in rps_games:
        await interaction.response.send_message("You are not currently in a game.")
        return

    game = rps_games[user_id]
    opponent_id = game["opponent"]
    rps_games[user_id]["choice"] = choice

    if opponent_id in rps_games and rps_games[opponent_id]["choice"]:
        opponent_choice = rps_games[opponent_id]["choice"]
        user_choice = rps_games[user_id]["choice"]

        if user_choice == opponent_choice:
            result = "It's a tie!"
        elif (user_choice == "rock" and opponent_choice == "scissors") or \
             (user_choice == "scissors" and opponent_choice == "paper") or \
             (user_choice == "paper" and opponent_choice == "rock"):
            result = f"{interaction.user.mention} wins!"
        else:
            result = f"<@{opponent_id}> wins!"

        await interaction.response.send_message(
            f"You played **{user_choice}**, <@{opponent_id}> played **{opponent_choice}**.\n{result}"
        )
        del rps_games[user_id]; del rps_games[opponent_id]
    else:
        await interaction.response.send_message("Your move has been recorded. Waiting for your opponent to play.")

# =========[ TIC TAC TOE ]=========
ttt_games = {}

@bot.tree.command(name="tictactoe", description="Start a Tic-Tac-Toe game (buttons, max 5x5, default 5x5, win with 4 in a row).")
async def tictactoe(interaction: discord.Interaction, opponent: discord.Member, size: int = 5, win_length: int = 4):
    if size < 3 or size > 5:
        await interaction.response.send_message("❌ Board size must be between 3 and 5 for button version.")
        return
    if win_length < 3 or win_length > size:
        await interaction.response.send_message("❌ Win length must be between 3 and the board size.")
        return
    if opponent.bot or opponent == interaction.user:
        await interaction.response.send_message("❌ You must challenge another human.")
        return
    if interaction.channel.id in ttt_games:
        await interaction.response.send_message("⚠️ A game is already active in this channel.", ephemeral=True)
        return

    board = [" "] * (size * size)
    ttt_games[interaction.channel.id] = {
        "board": board,
        "players": [interaction.user, opponent],
        "turn": interaction.user,
        "size": size,
        "win_length": win_length
    }

    await interaction.response.send_message(
        f"🎮 {interaction.user.mention} vs {opponent.mention} — {interaction.user.mention}'s turn on {size}x{size}, win with {win_length} in a row!",
        view=TicTacToeView(interaction.channel.id)
    )

class TicTacToeView(discord.ui.View):
    def __init__(self, channel_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        game = ttt_games[self.channel_id]
        board = game["board"]
        size = game["size"]

        for i in range(len(board)):
            label = board[i] if board[i] != " " else "·"
            row = i // size
            style = discord.ButtonStyle.primary if board[i] == " " else discord.ButtonStyle.gray
            disabled = board[i] != " "
            self.add_item(TTTButton(label=label, row=row, index=i, style=style, disabled=disabled))

class TTTButton(discord.ui.Button):
    def __init__(self, label, row, index, style, disabled):
        super().__init__(label=label, row=row, style=style, custom_id=str(index), disabled=disabled)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        game = ttt_games.get(interaction.channel.id)
        if not game:
            await interaction.response.send_message("❌ This game no longer exists.", ephemeral=True)
            return

        board = game["board"]
        current_turn = game["turn"]
        players = game["players"]
        size = game["size"]
        win_length = game["win_length"]

        if interaction.user != current_turn:
            await interaction.response.send_message("⛔ It's not your turn!", ephemeral=True)
            return
        if board[self.index] != " ":
            await interaction.response.send_message("That spot is already taken!", ephemeral=True)
            return

        mark = "X" if current_turn == players[0] else "O"
        board[self.index] = mark
        game["turn"] = players[1] if current_turn == players[0] else players[0]

        view = TicTacToeView(interaction.channel.id)
        text_board = render_text_board(board, size)

        if check_winner(board, size, self.index, win_length):
            del ttt_games[interaction.channel.id]
            view.add_item(RematchButton(players[0], players[1], size, win_length))
            await interaction.response.edit_message(
                content=f"🏆 {interaction.user.mention} ({mark}) wins!\n{text_board}",
                view=view
            )
        elif " " not in board:
            del ttt_games[interaction.channel.id]
            view.add_item(RematchButton(players[0], players[1], size, win_length))
            await interaction.response.edit_message(
                content=f"🤝 It's a draw!\n{text_board}",
                view=view
            )
        else:
            await interaction.response.edit_message(
                content=f"{game['turn'].mention}'s turn.\n{text_board}",
                view=view
            )

class RematchButton(discord.ui.Button):
    def __init__(self, p1, p2, size, win_length):
        super().__init__(label="🔁 Rematch", style=discord.ButtonStyle.success)
        self.p1 = p1; self.p2 = p2
        self.size = size; self.win_length = win_length

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.p1 and interaction.user != self.p2:
            await interaction.response.send_message("Only a player from the last game can request a rematch!", ephemeral=True)
            return
        if interaction.channel.id in ttt_games:
            await interaction.response.send_message("A new game is already active in this channel.", ephemeral=True)
            return

        board = [" "] * (self.size * self.size)
        ttt_games[interaction.channel.id] = {
            "board": board,
            "players": [self.p1, self.p2],
            "turn": self.p1,
            "size": self.size,
            "win_length": self.win_length
        }

        await interaction.response.edit_message(
            content=f"🎮 Rematch started between {self.p1.mention} and {self.p2.mention}! {self.p1.mention}'s turn.",
            view=TicTacToeView(interaction.channel.id)
        )

def check_winner(board, size, last_move, win_length):
    def get(x, y):
        return board[y * size + x] if 0 <= x < size and 0 <= y < size else None
    x0 = last_move % size
    y0 = last_move // size
    mark = get(x0, y0)

    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for dx, dy in directions:
        count = 1
        for dir in [-1, 1]:
            step = 1
            while True:
                x = x0 + dx * step * dir
                y = y0 + dy * step * dir
                if get(x, y) == mark:
                    count += 1
                    step += 1
                else:
                    break
        if count >= win_length:
            return True
    return False

def render_text_board(board, size):
    lines = []
    for y in range(size):
        row = board[y * size:(y + 1) * size]
        lines.append(" | ".join(cell if cell != " " else "." for cell in row))
    return "```\n" + "\n".join(lines) + "\n```"

# =========[ MESSAGE EVENTS / TTS ]=========
# Map emoji -> cách đọc (key sẽ được chuẩn hoá về lowercase)
EMOJI_READ_MAP = {
    "tre": "chê",
    "shock": "sốc",
    "cuoinhechmep": "cười nhếch mép",
    "buonqua": "buồn quá",
    "jztr": "gì dị trời",
    "mt_xiu": "xỉu",
    "6107pepeclap": "vỗ tay vỗ tay",
    "meu": "mếu",
    "rosewtf": "Rô giề oát đờ phắc",
    "jennieffs": "Chen ni nhức nhức cái đầu",
    "ajenniesmh": "chen ni lắc lắc đầu",
    "giay": "giãy đành đạch",
    "giaydanhdach": "giãy đành đạch đành đạch",
    "mt_camxuc": "Mít thy cảm xúc",
    "airenepout": "Ái Linh chu mỏ",
    "yerisad": "xúc động",
    "like": "ô kê nha",
    "doi~1": "Ngọi dỗi",
    "gianmisthy": "Gián mít thy là sao zị trời",
    "guongcuoi": "gượng cười",
    "embewow": "Ồ ồ ồ ooooooo",
    "ahahaha": "á há há há",
    "2like": "ô kê nha, lai nha",
    "ngat": "ngất",
    "chao": "chào",
    "suynghi": "si si nghĩ nghĩ",
    "chongnanh": "chống nhạnh",
    "detcoi": "để tau coi",
    "deroicoi": "để ròi coi",
    "dead": "trết",
    "ruvaysao": "rữ zị sao",
    "frogsus": "ếch đa nghi",
    "think0": "si nghĩ",
    "gotnuocmat": "gớt nước mắt",
    "doi": "dỗi",
    "aaaaaa": "aaaaaaaaaaaaaaaaaaaaaaaa",
    "dtty5sao": "tê oăn năm sao",
    "gaugau": "gâu gâu",
    "lasaonua": "là sao nữa",
    "sadgers": "pepe xúc động chực trào nước mắt",
    "hehehe": "e he he he he",
    "emoji_195": "na tra buồn ngủ",
    "doran_sohai": "đo ran sợ hãi",
    "pnv_doiroi~1": "dỗi gòi",
    "suy": "suy",
    "rosestare1": "Rô zề nhìn khinh bỉ",
    "vinhbiet": "vĩnh biệt cuộc đời",
    "block": "lóc",
    "zensob": "zen nít xu khóc lóc",
    "omduochong": "anh ơi em nữa",
    "que": "quê",
    "shock~1": "ze ri sốc",
    "aireneonly": "ạc ghẻ Ái Linh",
    "yerisad": "xúc động",
    "alisabored": "Lisa chán chả buồn nói",
    "roseawkward": "Rô giề sượng trân",
    "jenniepout": "chen ni chu mỏ",
    "mt_thatym": "mít thy thả tym",
    "mt_thatim": "mít thy thả tim",
    "reveluvbonk": "man đu bong bong bong",
    "takemymoney": "xòe tay ra",
    "yl_xoee": "cho em xin",
    "noinhanh": "nói nhanh",
    "rosedisgust": "rô giề thấy kinh tởm",
    "tretgoi": "trết gòi",
    "joynod": "rồi hiểu rồi gật gật",
    "andepkhong": "mày coi chừng tau",
    "aaaaa": "trời ơi tức quá",
    "chamkam": "ụ á chầm kẽm",
    "chemat": "hong tháy gì hớt, hong tháy gì hớt",
    "daa": "dạ",
    "echkhoc": "ếch khóc",
    "mute~1": "línnnn",
    "omg": "cọc rồi nha",
    "tucgian": "tức giận",
    "frog_hmm": "chắc chưa",
    "joymad": "Zoi hiểu không nổi",
    "prayge": "lạy trời",
    "aibietgi": "ai biết gì đâu",
    "chém gió": "San chém chém chém",
    "echcafe": "cóp phi",
    "hetcuu": "hết cíu",
    "hettien": "hớt tiền",
    "oeoe": "mắc óy",
    "nongquane": "nóng quá nè",
    "nono": "thôi đi nô nô nô",
    "tucgian~1": "dị con được hom",
    "daubung": "suy suy tư tư",
    "depko": "nín liền cho mẹ",
    "nanniah": "năng nỉ ó",
    
}
# Chuẩn hoá key lowercase (để map nhận cả tên emoji HOA/thường)
EMOJI_READ_MAP = { (k or "").lower(): v for k, v in EMOJI_READ_MAP.items() }

EMOJI_ANGLE_RE = re.compile(r"<a?:([A-Za-z0-9_]+):\d+>")
EMOJI_PLAINTEXT_RE = re.compile(r"(?<!<):([A-Za-z0-9_]+):(?!\d+>)")

def _desc_from_name(name: str) -> str:
    return EMOJI_READ_MAP.get((name or "").lower(), (name or "").replace("_", " "))

def preprocess_emoji_text(text: str, message: discord.Message):
    """
    Trả về (processed_text, emoji_desc_list, is_emoji_only_on_text)
    - processed_text: text đã thay emoji -> chữ
    - emoji_desc_list: danh sách mô tả emoji phát hiện trong 'text'
    - is_emoji_only_on_text: True nếu 'text' chỉ gồm emoji + khoảng trắng
    """
    original = text
    emoji_descs = []

    # emoji đã được discord parse
    for e in getattr(message, "emojis", []):
        token = str(e)      # "<:name:id>" / "<a:name:id>"
        name  = (e.name or "").lower()
        rep   = _desc_from_name(name)
        if token in text:
            emoji_descs.append(rep)
            text = text.replace(token, rep)

    # angle-bracket còn sót
    def repl_angle(m):
        rep = _desc_from_name(m.group(1))
        emoji_descs.append(rep)
        return rep
    text = EMOJI_ANGLE_RE.sub(repl_angle, text)

    # dạng :name:
    def repl_plain(m):
        rep = _desc_from_name(m.group(1))
        emoji_descs.append(rep)
        return rep
    text = EMOJI_PLAINTEXT_RE.sub(repl_plain, text)

    # Kiểm tra phần sau 'mt' có CHỈ emoji không
    only_emoji_stripped = EMOJI_ANGLE_RE.sub("", original)
    only_emoji_stripped = EMOJI_PLAINTEXT_RE.sub("", only_emoji_stripped)
    is_emoji_only = only_emoji_stripped.strip() == ""

    if os.getenv("DEBUG_TTS") == "1":
        print("RAW_AFTER_MT:", original)
        print("EMOJI_DESCS:", emoji_descs)
        print("TEXT_PROCESSED:", text)
        print("ONLY_EMOJI?", is_emoji_only)

    return text.strip(), emoji_descs, is_emoji_only

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()
    lang_codes = {"en", "vi", "es", "ko", "zh"}
    valid_rps = ["rock", "paper", "scissors"]

    if content.startswith("mtdr"):
        result = random.randint(1, 6)
        await message.channel.send(f"🎲 You rolled a {result}!")
    elif content.startswith("mtfc"):
        result = random.choice(["Heads", "Tails"])
        await message.channel.send(f"🪙 The coin landed on: **{result}**")
    elif content.startswith("mtrps"):
        parts = content.split()
        if len(parts) < 2 or parts[1] not in valid_rps:
            await message.channel.send("Please choose: rock, paper, or scissors.")
            return
        user_choice = parts[1]
        bot_choice = random.choice(valid_rps)
        if user_choice == bot_choice:
            result = "It's a tie!"
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "scissors" and bot_choice == "paper") or \
             (user_choice == "paper" and bot_choice == "rock"):
            result = "You win!"
        else:
            result = "You lose!"
        await message.channel.send(f"You chose **{user_choice}**, I chose **{bot_choice}**. {result}")
    elif content.startswith("mtrpsu"):
        await message.channel.send("Use `/rps_challenge @user` to start a PvP game!")

    # 🗣️ gTTS voice playback
    elif content.startswith("mt"):
        vc = discord.utils.get(bot.voice_clients, guild=message.guild)

        if vc and message.author.voice and message.author.voice.channel == vc.channel:
            try:
                parts = message.content.split()
                lang = "vi"
                text = ""

                if len(parts) >= 3 and parts[1] in lang_codes:
                    lang = parts[1]
                    text = " ".join(parts[2:])  # sau "mt <lang> ..."
                else:
                    text = message.content[3:].strip()  # sau "mt "

                processed, emoji_descs, only_emoji = preprocess_emoji_text(text, message)

                # Nếu chỉ gửi emoji -> đọc "<user> đã gửi emoji: ..."
                if only_emoji and emoji_descs:
                    processed = f"{message.author.display_name} gửi emoji: " + ", ".join(emoji_descs)

                if not processed.strip():
                    await message.channel.send("❌ Bạn chưa nhập nội dung cần nói.")
                    return

                ensure_dir("generated")
                out_path = "generated/message.mp3"

                tts = gTTS(text=processed, lang=lang)
                tts.save(out_path)

                if vc.is_playing():
                    while vc.is_playing():
                        await asyncio.sleep(0.5)

                vc.play(
                    FFmpegPCMAudio(out_path, executable=FFMPEG_PATH),
                    after=lambda e: print("✅ Finished speaking")
                )
                print(f"🎤 {message.author.display_name} said: {processed}")

            except Exception as e:
                print(f"gTTS message error: {e}")
        else:
            print(f"❌ {message.author.display_name} tried to TTS, but is not in the same VC as the bot.")

    await bot.process_commands(message)

# =========[ GREET / BYE TTS TRONG VOICE ]=========
async def play_gtts(text: str, filename: str, vc):
    try:
        ensure_dir("generated")
        path = os.path.join("generated", filename)

        tts = gTTS(text=text, lang="vi")
        tts.save(path)

        if vc.is_playing():
            while vc.is_playing():
                await asyncio.sleep(0.5)

        vc.play(
            FFmpegPCMAudio(path, executable=FFMPEG_PATH),
            after=lambda e: print(f"✅ Finished playing: {path}")
        )
    except Exception as e:
        print(f"gTTS playback error: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    vc = discord.utils.get(bot.voice_clients, guild=member.guild)

    if after.channel and vc and after.channel == vc.channel and before.channel != after.channel:
        await play_gtts(f"Xin chào {member.display_name}", "greeting.mp3", vc)
    elif before.channel and vc and before.channel == vc.channel and after.channel != vc.channel:
        await play_gtts(f"Tạm biệt {member.display_name}", "goodbye.mp3", vc)

# =========[ OPENAI COMMANDS ]=========
@bot.tree.command(name="ask", description="Ask the bot anything!")
async def ask(interaction: discord.Interaction, *, question: str):
    await interaction.response.defer()
    try:
        if client is None:
            await interaction.followup.send("OpenAI client chưa cấu hình.")
            return
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": question}]
        )
        answer = response.choices[0].message.content or "No answer."
        chunks = [answer[i:i+1990] for i in range(0, len(answer), 1990)]
        await interaction.followup.send(f"**❓ You asked:**\n`{question}`")
        for chunk in chunks:
            await interaction.followup.send(chunk)
    except Exception as e:
        await interaction.followup.send("An error occurred while fetching a response.")
        print(f"Error: {e}")

@bot.tree.command(name="speak", description="Convert text to speech using OpenAI (file only)")
async def speak(interaction: discord.Interaction, *, text: str):
    await interaction.response.defer()
    try:
        if client is None:
            await interaction.followup.send("OpenAI client chưa cấu hình.")
            return
        ensure_dir("generated")
        file_path = "generated/speech.mp3"
        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="nova",
            input=text
        ) as resp:
            resp.stream_to_file(file_path)

        await interaction.followup.send(
            content=f"🗣️ Your input: `{text}`",
            file=File(file_path)
        )
    except Exception as e:
        await interaction.followup.send("❌ Failed to generate speech.")
        print(f"OpenAI TTS error: {e}")

@bot.tree.command(name="generate_image", description="Generate an image based on a prompt.")
async def generate_image(interaction: discord.Interaction, *, prompt: str):
    await interaction.response.defer()
    try:
        if client is None:
            await interaction.followup.send("OpenAI client chưa cấu hình.")
            return
        ensure_dir("generated")
        result = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            n=1
        )
        image_url = result.data[0].url
        image_data = requests.get(image_url).content
        image_path = "generated/generated_image.png"
        with open(image_path, "wb") as f:
            f.write(image_data)

        await interaction.followup.send(
            content=f"**🖼️ Prompt:** `{prompt}`",
            file=File(image_path)
        )
    except Exception as e:
        await interaction.followup.send("Failed to generate an image.")
        print(f"Error: {e}")

@bot.tree.command(name="upload_file", description="Generate and upload a file with custom content.")
async def upload_file(interaction: discord.Interaction, *, content: str = "This is a sample file generated by the bot."):
    await interaction.response.defer()
    try:
        ensure_dir("generated")
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir="generated", suffix=".txt") as f:
            f.write(content)
            tmp_path = f.name
        await interaction.followup.send("Here is your generated file:", file=File(tmp_path))
    except Exception as e:
        await interaction.followup.send("Failed to generate the file.")
        print(f"Error: {e}")

@bot.tree.command(name="upload_pdf", description="Generate and upload a PDF file.")
async def upload_pdf(interaction: discord.Interaction, *, content: str = "This is a sample PDF file."):
    await interaction.response.defer()
    try:
        ensure_dir("generated")
        font_path = os.path.join("assets", "fonts", "DejaVuSans.ttf")
        if not os.path.isfile(font_path):
            await interaction.followup.send("❌ Missing font file for Unicode PDF (assets/fonts/DejaVuSans.ttf).")
            return

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=12)
        pdf.multi_cell(0, 8, content)

        fd, file_path = tempfile.mkstemp(prefix="generated_", suffix=".pdf", dir="generated")
        os.close(fd)
        pdf.output(file_path)

        await interaction.followup.send("Here is your generated PDF:", file=File(file_path))
    except Exception as e:
        await interaction.followup.send("Failed to generate the PDF.")
        print(f"Error: {e}")

# =========[ RUN ]=========
bot.run(TOKEN)
