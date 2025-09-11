# cogs/utils/permissions.py

import discord
from discord import app_commands

def has_guild_permissions(**perms):
    def predicate(interaction: discord.Interaction):
        if not interaction.guild:
            raise app_commands.errors.CheckFailure("This command can only be used in a server.")

        missing = [
            perm for perm, value in perms.items()
            if getattr(interaction.guild.me.guild_permissions, perm) != value
        ]
        if missing:
            raise app_commands.errors.CheckFailure(
                f"❌ Bot is missing permissions: {', '.join(missing)}"
            )
        return True
    return app_commands.check(predicate)
