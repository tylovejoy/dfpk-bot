import asyncio
import sys

import discord
from discord.ext import commands
import internal.constants as constants


async def confirm(ctx: commands.Context, message: discord.Message):
    """Create a confirm/cancel reaction menu.
    Return True or False depending on which reaction was clicked.

    If a timeout occurs, return None.
    """

    def check(r, u):
        """Check if reaction is from command author."""
        return (
            str(r.emoji)
            in (constants.CONFIRM_REACTION_EMOJI, constants.CANCEL_REACTION_EMOJI)
            and u.id == ctx.author.id
            and r.message.id == message.id
        )

    await message.add_reaction(constants.CONFIRM_REACTION_EMOJI)
    await message.add_reaction(constants.CANCEL_REACTION_EMOJI)

    try:
        reaction, user = await ctx.bot.wait_for("reaction_add", timeout=30, check=check)

        emoji = str(reaction.emoji)

        if emoji == constants.CONFIRM_REACTION_EMOJI:
            await message.clear_reactions()
            return True
        await message.clear_reactions()
        return False
    except asyncio.TimeoutError:
        await message.clear_reactions()
        return None
