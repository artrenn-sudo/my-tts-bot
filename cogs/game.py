import discord
import random
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button

class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rps_games = {}
        self.ttt_games = {}

    @app_commands.command(name="menu", description="Show game command menu")
    async def menu(self, interaction: discord.Interaction):
        await interaction.response.send_message("""
🎮 **Game Menu:**
- `/roll_dice [sides]` or `mtdr` — Roll a dice (default 6 sides)
- `/flip_coin` or `mtfc` — Flip a coin
- `/rps` or `mtrps` — Rock, Paper, Scissors vs bot
- `/rps_play` — Play PvP move
- `/tictactoe` — Tic-Tac-Toe
""")

    @app_commands.command(name="roll_dice", description="Roll a 6-sided dice with button.")
    async def roll_dice(self, interaction: discord.Interaction):
        class DiceView(View):
            @discord.ui.button(label="Roll 🎲", style=discord.ButtonStyle.primary)
            async def roll_button(self, interaction: discord.Interaction, button: Button):
                result = random.randint(1, 6)
                await interaction.response.edit_message(content=f"🎲 You rolled a **{result}**!", view=self)

        await interaction.response.send_message("Click the button to roll the dice!", view=DiceView())

    @app_commands.command(name="flip_coin", description="Flip a coin with button.")
    async def flip_coin(self, interaction: discord.Interaction):
        class CoinView(View):
            @discord.ui.button(label="Flip 🪙", style=discord.ButtonStyle.secondary)
            async def flip_button(self, interaction: discord.Interaction, button: Button):
                result = random.choice(["Heads", "Tails"])
                await interaction.response.edit_message(content=f"🪙 The coin landed on **{result}**!", view=self)

        await interaction.response.send_message("Click the button to flip a coin!", view=CoinView())

    @app_commands.command(name="rps", description="Play Rock, Paper, Scissors vs the bot.")
    async def rps(self, interaction: discord.Interaction):
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

    @app_commands.command(name="rps_play", description="Play your move in Rock, Paper, Scissors.")
    async def rps_play(self, interaction: discord.Interaction, choice: str):
        user_id = interaction.user.id
        valid_choices = ["rock", "paper", "scissors"]
        choice = choice.lower()

        if choice not in valid_choices:
            await interaction.response.send_message("Invalid choice. Use rock, paper, or scissors.")
            return

        if user_id not in self.rps_games:
            await interaction.response.send_message("You are not currently in a game.")
            return

        game = self.rps_games[user_id]
        opponent_id = game["opponent"]

        self.rps_games[user_id]["choice"] = choice

        if opponent_id in self.rps_games and self.rps_games[opponent_id]["choice"]:
            opponent_choice = self.rps_games[opponent_id]["choice"]
            user_choice = self.rps_games[user_id]["choice"]

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

            del self.rps_games[user_id]
            del self.rps_games[opponent_id]
        else:
            await interaction.response.send_message("Your move has been recorded. Waiting for your opponent to play.")

    @app_commands.command(name="tictactoe", description="Start a Tic-Tac-Toe game (buttons, max 5x5, default 5x5, win with 4 in a row).")
    async def tictactoe(self, interaction: discord.Interaction, opponent: discord.Member, size: int = 5, win_length: int = 4):
        if size < 3 or size > 5:
            await interaction.response.send_message("❌ Board size must be between 3 and 5 for button version.")
            return
        if win_length < 3 or win_length > size:
            await interaction.response.send_message("❌ Win length must be between 3 and the board size.")
            return
        if opponent.bot or opponent == interaction.user:
            await interaction.response.send_message("❌ You must challenge another human.")
            return
        if interaction.channel.id in self.ttt_games:
            await interaction.response.send_message("⚠️ A game is already active in this channel.", ephemeral=True)
            return

        board = [" "] * (size * size)
        self.ttt_games[interaction.channel.id] = {
            "board": board,
            "players": [interaction.user, opponent],
            "turn": interaction.user,
            "size": size,
            "win_length": win_length
        }

        await interaction.response.send_message(
            f"🎮 {interaction.user.mention} vs {opponent.mention} — {interaction.user.mention}'s turn on {size}x{size}, win with {win_length} in a row!",
            view=TicTacToeView(interaction.channel.id, self.ttt_games)
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.lower()
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

class TicTacToeView(discord.ui.View):
    def __init__(self, channel_id, ttt_games):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.ttt_games = ttt_games
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        game = self.ttt_games[self.channel_id]
        board = game["board"]
        size = game["size"]

        for i in range(len(board)):
            label = board[i] if board[i] != " " else "·"
            row = i // size
            style = discord.ButtonStyle.primary if board[i] == " " else discord.ButtonStyle.gray
            disabled = board[i] != " "
            self.add_item(TTTButton(label=label, row=row, index=i, style=style, disabled=disabled))

class TTTButton(discord.ui.Button):
    def __init__(self, label, row, index, style, disabled, ttt_games):
        super().__init__(label=label, row=row, style=style, custom_id=str(index), disabled=disabled)
        self.index = index
        self.ttt_games = ttt_games

    async def callback(self, interaction: discord.Interaction):
        game = self.ttt_games.get(interaction.channel.id)
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
            del self.ttt_games[interaction.channel.id]
            view.add_item(RematchButton(players[0], players[1], size, win_length))
            await interaction.response.edit_message(
                content=f"🏆 {interaction.user.mention} ({mark}) wins!\n{text_board}",
                view=view
            )
        elif " " not in board:
            del self.ttt_games[interaction.channel.id]
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
    def __init__(self, p1, p2, size, win_length, ttt_games):
        super().__init__(label="🔁 Rematch", style=discord.ButtonStyle.success)
        self.p1 = p1
        self.p2 = p2
        self.size = size
        self.win_length = win_length
        self.ttt_games = ttt_games

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.p1 and interaction.user != self.p2:
            await interaction.response.send_message("Only a player from the last game can request a rematch!", ephemeral=True)
            return

        if interaction.channel.id in self.ttt_games:
            await interaction.response.send_message("A new game is already active in this channel.", ephemeral=True)
            return

        board = [" "] * (self.size * self.size)
        self.ttt_games[interaction.channel.id] = {
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

# Setup
async def setup(bot):
    await bot.add_cog(GameCog(bot))

