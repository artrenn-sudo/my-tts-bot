import discord
import json
import os
import random
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

ECONOMY_FILE = "economy.json"

# Load economy data
def load_economy():
    if not os.path.exists(ECONOMY_FILE):
        with open(ECONOMY_FILE, "w") as f:
            json.dump({}, f)
    with open(ECONOMY_FILE, "r") as f:
        return json.load(f)

# Save economy data
def save_economy(economy):
    with open(ECONOMY_FILE, "w") as f:
        json.dump(economy, f, indent=4)

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = load_economy()

    def ensure_user(self, user_id):
        if str(user_id) not in self.economy:
            self.economy[str(user_id)] = {"balance": 0, "last_daily": None}

    # Balance
    @app_commands.command(name="balance", description="Check your coin balance.")
    async def balance(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        self.ensure_user(user_id)
        balance = self.economy[str(user_id)]["balance"]
        await interaction.response.send_message(f"💰 You have **{balance}** coins.")

    # Give
    @app_commands.command(name="give", description="Give coins to another user.")
    async def give(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        giver_id = interaction.user.id
        receiver_id = member.id

        if amount <= 0:
            await interaction.response.send_message("Amount must be positive.")
            return

        self.ensure_user(giver_id)
        self.ensure_user(receiver_id)

        if self.economy[str(giver_id)]["balance"] < amount:
            await interaction.response.send_message("You don't have enough coins.")
            return

        self.economy[str(giver_id)]["balance"] -= amount
        self.economy[str(receiver_id)]["balance"] += amount
        save_economy(self.economy)

        await interaction.response.send_message(
            f"💸 You gave **{amount}** coins to {member.mention}!"
        )

    # Work
    @app_commands.command(name="work", description="Work to earn some coins.")
    async def work(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        self.ensure_user(user_id)
        earnings = random.randint(50, 150)
        self.economy[str(user_id)]["balance"] += earnings
        save_economy(self.economy)
        await interaction.response.send_message(f"🛠️ You worked and earned **{earnings}** coins!")

    # Daily
    @app_commands.command(name="daily", description="Claim your daily reward.")
    async def daily(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        self.ensure_user(user_id)

        last_daily = self.economy[str(user_id)]["last_daily"]
        now = datetime.utcnow()

        if last_daily:
            last_daily_time = datetime.strptime(last_daily, "%Y-%m-%d %H:%M:%S")
            if now - last_daily_time < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last_daily_time)
                hours, remainder = divmod(remaining.seconds, 3600)
                minutes = remainder // 60
                await interaction.response.send_message(
                    f"⏳ You already claimed your daily reward. Try again in **{remaining.days}d {hours}h {minutes}m**."
                )
                return

        reward = 200
        self.economy[str(user_id)]["balance"] += reward
        self.economy[str(user_id)]["last_daily"] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_economy(self.economy)
        await interaction.response.send_message(f"🎁 You claimed your daily reward: **{reward}** coins!")

    # Leaderboard
    @app_commands.command(name="leaderboard", description="Show the top richest users.")
    async def leaderboard(self, interaction: discord.Interaction):
        sorted_users = sorted(
            self.economy.items(), key=lambda x: x[1]["balance"], reverse=True
        )[:10]

        embed = discord.Embed(title="🏆 Top 10 Richest Users", color=discord.Color.gold())
        for idx, (user_id, data) in enumerate(sorted_users, start=1):
            user = interaction.guild.get_member(int(user_id))
            name = user.display_name if user else f"User {user_id}"
            balance = data["balance"]
            embed.add_field(
                name=f"#{idx} {name}", value=f"💰 **{balance}** coins", inline=False
            )

        await interaction.response.send_message(embed=embed)

    # Listener - message aliases
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.lower()
        user_id = message.author.id
        self.ensure_user(user_id)

        # mgive
        if content.startswith("mgive"):
            parts = message.content.split()
            if len(parts) < 3 or not parts[2].isdigit() or not message.mentions:
                await message.channel.send("Usage: mgive @user amount")
                return
            receiver = message.mentions[0]
            amount = int(parts[2])

            if amount <= 0:
                await message.channel.send("Amount must be positive.")
                return

            if self.economy[str(user_id)]["balance"] < amount:
                await message.channel.send("You don't have enough coins.")
                return

            self.ensure_user(receiver.id)
            self.economy[str(user_id)]["balance"] -= amount
            self.economy[str(receiver.id)]["balance"] += amount
            save_economy(self.economy)

            await message.channel.send(
                f"💸 You gave **{amount}** coins to {receiver.mention}!"
            )

        # mbal or mcash
        elif content.startswith("mbal") or content.startswith("mcash"):
            balance = self.economy[str(user_id)]["balance"]
            await message.channel.send(f"💰 You have **{balance}** coins.")

        # mwork
        elif content.startswith("mwork"):
            earnings = random.randint(50, 150)
            self.economy[str(user_id)]["balance"] += earnings
            save_economy(self.economy)
            await message.channel.send(f"🛠️ You worked and earned **{earnings}** coins!")

        # mdaily
        elif content.startswith("mdaily"):
            last_daily = self.economy[str(user_id)]["last_daily"]
            now = datetime.utcnow()

            if last_daily:
                last_daily_time = datetime.strptime(last_daily, "%Y-%m-%d %H:%M:%S")
                if now - last_daily_time < timedelta(hours=24):
                    remaining = timedelta(hours=24) - (now - last_daily_time)
                    hours, remainder = divmod(remaining.seconds, 3600)
                    minutes = remainder // 60
                    await message.channel.send(
                        f"⏳ You already claimed your daily reward. Try again in **{remaining.days}d {hours}h {minutes}m**."
                    )
                    return

            reward = 200
            self.economy[str(user_id)]["balance"] += reward
            self.economy[str(user_id)]["last_daily"] = now.strftime("%Y-%m-%d %H:%M:%S")
            save_economy(self.economy)
            await message.channel.send(f"🎁 You claimed your daily reward: **{reward}** coins!")

        # mleaderboard
        elif content.startswith("mleaderboard"):
            sorted_users = sorted(
                self.economy.items(), key=lambda x: x[1]["balance"], reverse=True
            )[:10]

            embed = discord.Embed(title="🏆 Top 10 Richest Users", color=discord.Color.gold())
            for idx, (user_id, data) in enumerate(sorted_users, start=1):
                user = message.guild.get_member(int(user_id))
                name = user.display_name if user else f"User {user_id}"
                balance = data["balance"]
                embed.add_field(
                    name=f"#{idx} {name}", value=f"💰 **{balance}** coins", inline=False
                )

            await message.channel.send(embed=embed)

        # mrob
        elif content.startswith("mrob"):
            target_mentions = message.mentions
            if not target_mentions:
                await message.channel.send("Usage: mrob @user")
                return

            victim = target_mentions[0]
            victim_id = victim.id

            if victim_id == user_id:
                await message.channel.send("You can't rob yourself!")
                return

            self.ensure_user(victim_id)
            victim_balance = self.economy[str(victim_id)]["balance"]

            if victim_balance < 100:
                await message.channel.send("Target does not have enough coins to rob! (min 100)")
                return

            success = random.choice([True, False])

            if success:
                stolen_amount = min(200, victim_balance // 2)
                self.economy[str(user_id)]["balance"] += stolen_amount
                self.economy[str(victim_id)]["balance"] -= stolen_amount
                save_economy(self.economy)
                await message.channel.send(
                    f"🕵️ You successfully robbed **{stolen_amount}** coins from {victim.mention}!"
                )
            else:
                penalty = random.randint(50, 150)
                penalty = min(penalty, self.economy[str(user_id)]["balance"])
                self.economy[str(user_id)]["balance"] -= penalty
                save_economy(self.economy)
                await message.channel.send(
                    f"🚓 You got caught trying to rob! Lost **{penalty}** coins as a fine."
                )

        # mslot
        elif content.startswith("mslot"):
            bet = 100
            balance = self.economy[str(user_id)]["balance"]

            if balance < bet:
                await message.channel.send("You need at least 100 coins to play!")
                return

            self.economy[str(user_id)]["balance"] -= bet

            symbols = ["🍒", "🍋", "🔔", "⭐", "🍇"]
            result = [random.choice(symbols) for _ in range(3)]
            save_economy(self.economy)

            if result[0] == result[1] == result[2]:
                winnings = 300
                self.economy[str(user_id)]["balance"] += winnings
                save_economy(self.economy)
                await message.channel.send(
                    f"🎰 {' '.join(result)}\n**Jackpot!** You won **{winnings}** coins!"
                )
            else:
                await message.channel.send(
                    f"🎰 {' '.join(result)}\nYou lost **{bet}** coins. Better luck next time!"
                )

        # mcoinflip
        elif content.startswith("mcoinflip"):
            parts = message.content.split()
            if len(parts) < 3 or not parts[2].isdigit():
                await message.channel.send("Usage: mcoinflip heads/tails amount")
                return

            side = parts[1].lower()
            amount = int(parts[2])

            if side not in ["heads", "tails"]:
                await message.channel.send("Choose either **heads** or **tails**.")
                return

            if amount <= 0:
                await message.channel.send("Amount must be positive.")
                return

            if self.economy[str(user_id)]["balance"] < amount:
                await message.channel.send("You don't have enough coins.")
                return

            self.economy[str(user_id)]["balance"] -= amount

            flip_result = random.choice(["heads", "tails"])
            save_economy(self.economy)

            if side == flip_result:
                winnings = amount * 2
                self.economy[str(user_id)]["balance"] += winnings
                save_economy(self.economy)
                await message.channel.send(
                    f"🪙 Coin landed on **{flip_result}**! You won **{winnings}** coins!"
                )
            else:
                await message.channel.send(
                    f"🪙 Coin landed on **{flip_result}**. You lost **{amount}** coins."
                )
        # mhelp economy
        elif content.startswith("mhelp"):
            embed = discord.Embed(
                title="🪙 Economy Commands Help",
                description="List of available economy commands and shortcuts:",
                color=discord.Color.green()
            )
            embed.add_field(name="Check balance", value="`/balance`, `mbal`, `mcash`", inline=False)
            embed.add_field(name="Give coins", value="`/give @user amount`, `mgive @user amount`", inline=False)
            embed.add_field(name="Work", value="`/work`, `mwork`", inline=False)
            embed.add_field(name="Daily reward", value="`/daily`, `mdaily`", inline=False)
            embed.add_field(name="Leaderboard", value="`/leaderboard`, `mleaderboard`", inline=False)
            embed.add_field(name="Rob a user", value="`mrob @user`", inline=False)
            embed.add_field(name="Slot machine", value="`mslot`", inline=False)
            embed.add_field(name="Coin flip", value="`mcoinflip heads/tails amount`", inline=False)
            embed.add_field(name="Profile", value="`mprofile`", inline=False)
            await message.channel.send(embed=embed)

        # mprofile
        elif content.startswith("mprofile"):
            user = message.author
            self.ensure_user(user.id)
            balance = self.economy[str(user.id)]["balance"]

            embed = discord.Embed(
                title=f"🎫 Profile of {user.display_name}",
                color=discord.Color.purple()
            )
            embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            embed.add_field(name="💰 Balance", value=f"**{balance}** coins", inline=True)
            embed.add_field(name="🆔 User ID", value=f"`{user.id}`", inline=True)
            embed.set_footer(text="Economy System • Powered by your bot")
            await message.channel.send(embed=embed)

# Setup
async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
