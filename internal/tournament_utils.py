import logging
import sys
import discord
from disputils import BotEmbedPaginator

from database.BonusData import BonusData
from database.HardcoreData import HardcoreData
from database.MildcoreData import MildcoreData
from database.TimeAttackData import TimeAttackData
from internal.pb_utils import display_record

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot, constants
else:
    from internal import constants_bot_prod as constants_bot


def category_sort(message):
    if message.channel.id == constants_bot.TA_CHANNEL_ID:
        which_category = "TIMEATTACK"
    elif message.channel.id == constants_bot.MC_CHANNEL_ID:
        which_category = "MILDCORE"
    elif message.channel.id == constants_bot.HC_CHANNEL_ID:
        which_category = "HARDCORE"
    elif message.channel.id == constants_bot.BONUS_CHANNEL_ID:
        which_category = "BONUS"
    else:
        return None
    return which_category


async def tournament_boards(ctx, category):
    """Display boards for scoreboard and leaderboard commands."""
    count = 0
    embed = discord.Embed(title=f"{category}")
    embeds = []

    if category == "TIMEATTACK":
        _data_category = TimeAttackData
    elif category == "MILDCORE":
        _data_category = MildcoreData
    elif category == "HARDCORE":
        _data_category = HardcoreData
    else:  # "BONUS"
        _data_category = BonusData

    data_amount = await _data_category.count_documents()

    async for entry in _data_category.find().sort("record", 1):
        embed.add_field(
            name=f"#{count + 1} - {discord.utils.find(lambda m: m.id == entry.posted_by, ctx.guild.members)}",
            value=f"> Record: {display_record(entry.record)}\n",
            inline=False,
        )
        if (count + 1) % 10 == 0 or (count + 1) == data_amount:
            embeds.append(embed)
            embed = discord.Embed(title=category)

        count += 1

    if embeds:
        paginator = BotEmbedPaginator(ctx, embeds)
        await paginator.run()
    else:
        await ctx.send(f"No times exist for the {category.lower()} tournament!")
