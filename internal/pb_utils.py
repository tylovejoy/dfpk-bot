import discord

from database.WorldRecords import WorldRecords
from internal import utilities, test_constants as constants


async def boards(ctx, map_code, level, title, query):
    """Display boards for scoreboard and leaderboard commands."""
    count = 1
    exists = False
    embed = discord.Embed(title=f"{title}")
    async for entry in WorldRecords.find(query).sort("record", 1).limit(10):
        exists = True
        embed.add_field(
            name=f"#{count} - {entry.name}",
            value=(
                f"> Record: {utilities.display_record(entry.record)}\n"
                f"> Verified: {constants.VERIFIED_EMOJI if entry.verified is True else constants.NOT_VERIFIED_EMOJI}"
            ),
            inline=False,
        )
        count += 1
    if exists:
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No scoreboard for {map_code} level {level.upper()}!")
